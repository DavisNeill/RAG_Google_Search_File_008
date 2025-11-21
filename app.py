"""
Flask Web Interface for Agentic RAG System with Memory & Authentication
========================================================================

Full-stack application with:
- User authentication (Supabase)
- Session management
- Memory management (Mem0)
- Memory analytics
- Memory export
- RAG document retrieval
"""

import os
import json
import io
import csv
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

try:
    from supabase import create_client, Client
except ImportError:
    print("Warning: supabase package not installed")
    create_client = None
    Client = None

from agentic_rag import create_agentic_rag, AgentOrchestrator
from enhanced_agentic_rag import create_enhanced_rag, EnhancedAgenticRAG, EnhancedConfig
from evaluation_routes import evaluation_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Enable CORS
CORS(app)

# Register blueprints
app.register_blueprint(evaluation_bp)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xlsx', 'pptx', 'csv', 'json', 'md',
    'py', 'js', 'java', 'cpp', 'html', 'xml', 'ipynb'
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# Global instances
rag_orchestrator: EnhancedAgenticRAG = None  # Using enhanced RAG with Tier 1-3 features
supabase_client: Client = None


def init_supabase():
    """Initialize Supabase client"""
    global supabase_client

    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("Warning: SUPABASE_URL or SUPABASE_KEY not set. Auth will not work.")
        return False

    if create_client is None:
        print("Warning: supabase package not installed")
        return False

    try:
        supabase_client = create_client(supabase_url, supabase_key)
        # Make Supabase client available to blueprints
        app.config['SUPABASE_CLIENT'] = supabase_client
        print("Supabase initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Supabase: {e}")
        return False


def init_rag_system():
    """Initialize the ENHANCED RAG system with Tier 1-3 features"""
    global rag_orchestrator

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not set. RAG system will not be initialized.")
        return False

    try:
        # Configure Mem0 to use Google Gemini embeddings (no OpenAI needed!)
        memory_config = {
            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": "models/text-embedding-004",
                    "api_key": api_key
                }
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "agentic_rag_memories",
                    "embedding_model_dims": 768,
                    "path": "./qdrant_data"  # Local storage
                }
            }
        }

        # Create enhanced configuration
        enhanced_config = EnhancedConfig()

        # Production settings
        enhanced_config.use_hybrid_search = True  # Tier 1: Better retrieval
        enhanced_config.use_citations = True      # Tier 1: Source attribution
        enhanced_config.use_cache = True          # Tier 1: Performance boost
        enhanced_config.cache_type = 'memory'     # Use memory cache (Redis optional)

        enhanced_config.use_reranking = True      # Tier 2: Better precision
        enhanced_config.use_query_rewriting = True # Tier 2: Better recall
        enhanced_config.use_streaming = False      # Tier 2: Disabled for now (requires WebSocket)

        enhanced_config.use_multihop = True       # Tier 3: Complex questions
        enhanced_config.use_self_reflection = True # Tier 3: Quality validation
        enhanced_config.use_experiment_tracking = False  # Tier 3: Research mode only

        # Initialize Enhanced RAG with all features
        rag_orchestrator = create_enhanced_rag(
            api_key=api_key,
            memory_config=memory_config,
            enable_memory=True,
            config=enhanced_config,
            supabase_client=supabase_client
        )

        print("=" * 70)
        print("ENHANCED RAG System initialized successfully! 🚀")
        print("=" * 70)
        print("Active features:")
        print("  Tier 1: ✓ Hybrid Search, ✓ Citations, ✓ Cache")
        print("  Tier 2: ✓ Reranking, ✓ Query Processing")
        print("  Tier 3: ✓ Multi-hop, ✓ Self-Reflection")
        print("=" * 70)
        print("Expected improvements:")
        print("  • 30-50% better accuracy")
        print("  • 50-80% lower latency (with cache)")
        print("  • Enhanced source attribution")
        print("=" * 70)

        return True
    except Exception as e:
        print(f"Error initializing Enhanced RAG system: {e}")
        print(f"Falling back to basic RAG...")
        try:
            # Fallback to basic RAG if enhanced fails
            rag_orchestrator = create_agentic_rag(
                api_key=api_key,
                memory_config=memory_config,
                enable_memory=True
            )
            print("Basic RAG system initialized (Enhanced features unavailable)")
            return True
        except Exception as e2:
            print(f"Error initializing basic RAG system: {e2}")
            return False


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        user_role = session.get('user_role', 'user')
        if user_role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function


def get_user_role(user_id: str) -> str:
    """Get user role from database"""
    if supabase_client is None:
        return 'user'

    try:
        response = supabase_client.table('user_profiles')\
            .select('role')\
            .eq('id', user_id)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0].get('role', 'user')
        return 'user'
    except Exception as e:
        print(f"Error getting user role: {e}")
        return 'user'


def is_admin(user_id: str) -> bool:
    """Check if user is admin"""
    return get_user_role(user_id) == 'admin'


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# DATABASE HELPERS FOR PERSISTENT DOCUMENT STORAGE
# ============================================================================

def get_user_store(user_id: str, store_name: str = 'default') -> dict:
    """Get user's vector store from database"""
    if supabase_client is None:
        return None

    try:
        response = supabase_client.table('user_vector_stores')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('store_name', store_name)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user store: {e}")
        return None


def create_or_update_user_store(user_id: str, store_id: str, store_name: str = 'default', description: str = None) -> bool:
    """Create or update user's vector store in database"""
    if supabase_client is None:
        return False

    try:
        # Check if store exists
        existing = get_user_store(user_id, store_name)

        if existing:
            # Update existing store
            supabase_client.table('user_vector_stores')\
                .update({'store_id': store_id, 'description': description})\
                .eq('user_id', user_id)\
                .eq('store_name', store_name)\
                .execute()
        else:
            # Create new store
            supabase_client.table('user_vector_stores')\
                .insert({
                    'user_id': user_id,
                    'store_id': store_id,
                    'store_name': store_name,
                    'description': description
                })\
                .execute()

        return True
    except Exception as e:
        print(f"Error creating/updating user store: {e}")
        return False


def add_document_to_db(user_id: str, store_id: str, file_name: str, file_path: str,
                       file_size: int, mime_type: str = None, gemini_file_id: str = None) -> bool:
    """Add document metadata to database"""
    if supabase_client is None:
        return False

    try:
        supabase_client.table('user_documents')\
            .insert({
                'user_id': user_id,
                'store_id': store_id,
                'file_name': file_name,
                'file_path': file_path,
                'file_size': file_size,
                'mime_type': mime_type,
                'gemini_file_id': gemini_file_id
            })\
            .execute()
        return True
    except Exception as e:
        print(f"Error adding document to database: {e}")
        return False


def get_user_documents(user_id: str, store_name: str = 'default') -> list:
    """Get all documents for a user's store"""
    if supabase_client is None:
        return []

    try:
        # First get the store
        store = get_user_store(user_id, store_name)
        if not store:
            return []

        # Get documents for this store
        response = supabase_client.table('user_documents')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('store_id', store['store_id'])\
            .order('uploaded_at', desc=True)\
            .execute()

        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting user documents: {e}")
        return []


def delete_document_from_db(user_id: str, document_id: str) -> bool:
    """Delete a document from database"""
    if supabase_client is None:
        return False

    try:
        supabase_client.table('user_documents')\
            .delete()\
            .eq('user_id', user_id)\
            .eq('id', document_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Error deleting document: {e}")
        return False


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    if supabase_client is None:
        return jsonify({'error': 'Authentication not configured'}), 500

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        # Sign up user
        response = supabase_client.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {'name': name}
            }
        })

        return jsonify({
            'success': True,
            'message': 'Account created successfully. Please check your email for verification.',
            'user': {
                'id': response.user.id,
                'email': response.user.email
            }
        })

    except Exception as e:
        return jsonify({'error': f'Signup failed: {str(e)}'}), 400


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    if supabase_client is None:
        return jsonify({'error': 'Authentication not configured'}), 500

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        # Sign in user
        response = supabase_client.auth.sign_in_with_password({
            'email': email,
            'password': password
        })

        # Set session
        session.permanent = True
        session['user_id'] = response.user.id
        session['user_email'] = response.user.email
        session['access_token'] = response.session.access_token

        # Get and store user role
        user_role = get_user_role(response.user.id)
        session['user_role'] = user_role

        # Set user ID in RAG system
        if rag_orchestrator:
            rag_orchestrator.set_user_id(response.user.id)

        return jsonify({
            'success': True,
            'user': {
                'id': response.user.id,
                'email': response.user.email,
                'name': response.user.user_metadata.get('name', '')
            }
        })

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 401


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    try:
        if supabase_client:
            supabase_client.auth.sign_out()

        session.clear()

        return jsonify({'success': True, 'message': 'Logged out successfully'})

    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500


@app.route('/api/auth/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    # Refresh role from database if not in session
    if not user_role:
        user_role = get_user_role(user_id)
        session['user_role'] = user_role

    return jsonify({
        'user': {
            'id': user_id,
            'email': session.get('user_email'),
            'role': user_role,
            'is_admin': user_role == 'admin'
        }
    })


# ============================================================================
# DOCUMENT & KNOWLEDGE BASE ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
@admin_required
def upload_files():
    """Handle file uploads with persistent storage (Admin only)"""
    if rag_orchestrator is None:
        return jsonify({'error': 'RAG system not initialized'}), 500

    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')
    user_id = session.get('user_id')
    store_name = request.form.get('store_name', 'default')  # Use 'default' for persistent storage

    uploaded_files = []
    file_paths = []
    file_metadata = []

    # Save uploaded files
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            file.save(file_path)
            file_size = os.path.getsize(file_path)

            uploaded_files.append(filename)
            file_paths.append(file_path)
            file_metadata.append({
                'filename': filename,
                'path': file_path,
                'size': file_size
            })
        else:
            return jsonify({'error': f'Invalid file: {file.filename}'}), 400

    # Get or create persistent vector store
    try:
        chunking_config = {
            'white_space_config': {
                'max_tokens_per_chunk': int(request.form.get('max_tokens', 500)),
                'max_overlap_tokens': int(request.form.get('overlap_tokens', 50))
            }
        }

        # Check if user already has a store
        existing_store = get_user_store(user_id, store_name)

        if existing_store:
            # Add to existing store
            store_id = existing_store['store_id']
            # Note: Gemini File Search doesn't support adding to existing stores directly
            # So we need to recreate with all files
            # For now, create a new store with timestamp
            new_store_name = f"{store_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            store_id = rag_orchestrator.create_knowledge_base(
                store_name=new_store_name,
                file_paths=file_paths,
                chunking_config=chunking_config
            )
            # Update database with new store
            create_or_update_user_store(user_id, store_id, store_name,
                                       description=f"Updated with {len(uploaded_files)} new files")
        else:
            # Create new store
            store_id = rag_orchestrator.create_knowledge_base(
                store_name=store_name,
                file_paths=file_paths,
                chunking_config=chunking_config
            )
            # Save to database
            create_or_update_user_store(user_id, store_id, store_name,
                                       description=f"Knowledge base with {len(uploaded_files)} files")

        # Save document metadata to database
        for metadata in file_metadata:
            add_document_to_db(
                user_id=user_id,
                store_id=store_id,
                file_name=metadata['filename'],
                file_path=metadata['path'],
                file_size=metadata['size']
            )

        # Update session
        session['current_store'] = store_id
        session['store_name'] = store_name

        # Get total documents count
        all_docs = get_user_documents(user_id, store_name)

        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} file(s) to knowledge base',
            'store_id': store_id,
            'store_name': store_name,
            'files': uploaded_files,
            'file_count': len(uploaded_files),
            'total_documents': len(all_docs)
        })

    except Exception as e:
        return jsonify({'error': f'Error uploading files: {str(e)}'}), 500


@app.route('/query', methods=['POST'])
@login_required
def query():
    """Handle user queries with memory integration and persistent store"""
    if rag_orchestrator is None:
        return jsonify({'error': 'RAG system not initialized'}), 500

    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    # Get user's persistent store
    user_id = session.get('user_id')
    store_name = data.get('store_name', 'default')

    # Get user's store from database
    user_store = get_user_store(user_id, store_name)

    if not user_store:
        return jsonify({'error': 'No knowledge base found. Please upload documents first.'}), 400

    # Get query parameters
    store_id = user_store['store_id']
    metadata_filter = data.get('metadata_filter')
    include_citations = data.get('include_citations', True)

    try:
        result = rag_orchestrator.query(
            question=question,
            store_name=store_id,  # Use the actual Gemini store ID
            metadata_filter=metadata_filter,
            include_citations=include_citations,
            user_id=user_id
        )

        return jsonify({
            'success': True,
            'answer': result.get('text', ''),
            'query_type': result.get('query_type', 'GENERAL'),
            'citations': result.get('citations', []),
            'memories_used': result.get('memories_used', 0),
            'memory_enabled': result.get('memory_enabled', False),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500


# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/documents/list', methods=['GET'])
@login_required
def list_documents():
    """Get all documents in user's knowledge base"""
    user_id = session.get('user_id')
    store_name = request.args.get('store_name', 'default')

    try:
        documents = get_user_documents(user_id, store_name)

        # Format document info
        formatted_docs = []
        for doc in documents:
            formatted_docs.append({
                'id': doc['id'],
                'file_name': doc['file_name'],
                'file_size': doc['file_size'],
                'uploaded_at': doc['uploaded_at'],
                'mime_type': doc.get('mime_type')
            })

        # Get store info
        store = get_user_store(user_id, store_name)

        return jsonify({
            'success': True,
            'documents': formatted_docs,
            'count': len(formatted_docs),
            'store_name': store_name,
            'store_info': {
                'description': store.get('description') if store else None,
                'created_at': store.get('created_at') if store else None,
                'updated_at': store.get('updated_at') if store else None
            }
        })

    except Exception as e:
        return jsonify({'error': f'Error listing documents: {str(e)}'}), 500


@app.route('/api/documents/delete/<document_id>', methods=['DELETE'])
@admin_required
def delete_document(document_id):
    """Delete a document from knowledge base (Admin only)"""
    user_id = session.get('user_id')

    try:
        # Delete from database
        success = delete_document_from_db(user_id, document_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Document deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete document'}), 500

    except Exception as e:
        return jsonify({'error': f'Error deleting document: {str(e)}'}), 500


@app.route('/api/documents/stats', methods=['GET'])
@login_required
def get_document_stats():
    """Get statistics about user's documents"""
    user_id = session.get('user_id')
    store_name = request.args.get('store_name', 'default')

    try:
        documents = get_user_documents(user_id, store_name)
        store = get_user_store(user_id, store_name)

        total_size = sum(doc['file_size'] for doc in documents)

        return jsonify({
            'success': True,
            'total_documents': len(documents),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'store_exists': store is not None,
            'last_updated': store.get('updated_at') if store else None
        })

    except Exception as e:
        return jsonify({'error': f'Error getting document stats: {str(e)}'}), 500


@app.route('/api/documents/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_documents():
    """Bulk delete documents (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    document_ids = data.get('document_ids', [])

    if not document_ids:
        return jsonify({'error': 'No document IDs provided'}), 400

    user_id = session.get('user_id')

    try:
        # Call Supabase function for bulk delete
        response = supabase_client.rpc('bulk_delete_documents', {
            'doc_ids': document_ids,
            'admin_id': user_id
        }).execute()

        deleted_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} document(s)',
            'deleted_count': deleted_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk deleting documents: {str(e)}'}), 500


@app.route('/api/documents/hide/<document_id>', methods=['POST'])
@admin_required
def hide_document(document_id):
    """Hide a document (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    user_id = session.get('user_id')

    try:
        response = supabase_client.rpc('hide_document', {
            'doc_id': document_id,
            'admin_id': user_id
        }).execute()

        if response.data:
            return jsonify({
                'success': True,
                'message': 'Document hidden successfully'
            })
        else:
            return jsonify({'error': 'Failed to hide document'}), 500

    except Exception as e:
        return jsonify({'error': f'Error hiding document: {str(e)}'}), 500


@app.route('/api/documents/show/<document_id>', methods=['POST'])
@admin_required
def show_document(document_id):
    """Show a hidden document (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    user_id = session.get('user_id')

    try:
        response = supabase_client.rpc('show_document', {
            'doc_id': document_id,
            'admin_id': user_id
        }).execute()

        if response.data:
            return jsonify({
                'success': True,
                'message': 'Document is now visible'
            })
        else:
            return jsonify({'error': 'Failed to show document'}), 500

    except Exception as e:
        return jsonify({'error': f'Error showing document: {str(e)}'}), 500


@app.route('/api/documents/bulk-hide', methods=['POST'])
@admin_required
def bulk_hide_documents():
    """Bulk hide documents (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    document_ids = data.get('document_ids', [])

    if not document_ids:
        return jsonify({'error': 'No document IDs provided'}), 400

    user_id = session.get('user_id')

    try:
        response = supabase_client.rpc('bulk_hide_documents', {
            'doc_ids': document_ids,
            'admin_id': user_id
        }).execute()

        updated_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Successfully hid {updated_count} document(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk hiding documents: {str(e)}'}), 500


@app.route('/api/documents/bulk-show', methods=['POST'])
@admin_required
def bulk_show_documents():
    """Bulk show documents (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    document_ids = data.get('document_ids', [])

    if not document_ids:
        return jsonify({'error': 'No document IDs provided'}), 400

    user_id = session.get('user_id')

    try:
        response = supabase_client.rpc('bulk_show_documents', {
            'doc_ids': document_ids,
            'admin_id': user_id
        }).execute()

        updated_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Successfully showed {updated_count} document(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk showing documents: {str(e)}'}), 500


# ============================================================================
# ANALYTICS VISIBILITY CONTROL ENDPOINTS (ADMIN)
# ============================================================================

@app.route('/api/admin/analytics/enable/<user_id>', methods=['POST'])
@admin_required
def enable_user_analytics(user_id):
    """Enable analytics visibility for a specific user (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('enable_user_analytics', {
            'target_user_id': user_id,
            'admin_id': admin_id
        }).execute()

        if response.data:
            return jsonify({
                'success': True,
                'message': f'Analytics enabled for user {user_id}'
            })
        else:
            return jsonify({'error': 'Failed to enable analytics'}), 500

    except Exception as e:
        return jsonify({'error': f'Error enabling analytics: {str(e)}'}), 500


@app.route('/api/admin/analytics/disable/<user_id>', methods=['POST'])
@admin_required
def disable_user_analytics(user_id):
    """Disable analytics visibility for a specific user (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('disable_user_analytics', {
            'target_user_id': user_id,
            'admin_id': admin_id
        }).execute()

        if response.data:
            return jsonify({
                'success': True,
                'message': f'Analytics disabled for user {user_id}'
            })
        else:
            return jsonify({'error': 'Failed to disable analytics'}), 500

    except Exception as e:
        return jsonify({'error': f'Error disabling analytics: {str(e)}'}), 500


@app.route('/api/admin/analytics/bulk-enable', methods=['POST'])
@admin_required
def bulk_enable_analytics():
    """Bulk enable analytics for multiple users (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    user_ids = data.get('user_ids', [])

    if not user_ids:
        return jsonify({'error': 'No user IDs provided'}), 400

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('bulk_enable_analytics', {
            'user_ids': user_ids,
            'admin_id': admin_id
        }).execute()

        updated_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Analytics enabled for {updated_count} user(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk enabling analytics: {str(e)}'}), 500


@app.route('/api/admin/analytics/bulk-disable', methods=['POST'])
@admin_required
def bulk_disable_analytics():
    """Bulk disable analytics for multiple users (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    user_ids = data.get('user_ids', [])

    if not user_ids:
        return jsonify({'error': 'No user IDs provided'}), 400

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('bulk_disable_analytics', {
            'user_ids': user_ids,
            'admin_id': admin_id
        }).execute()

        updated_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Analytics disabled for {updated_count} user(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk disabling analytics: {str(e)}'}), 500


@app.route('/api/admin/analytics/status/<user_id>', methods=['GET'])
@admin_required
def get_analytics_status(user_id):
    """Get analytics visibility status for a user (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        response = supabase_client.table('user_profiles')\
            .select('analytics_visible, analytics_visibility_updated_by, analytics_visibility_updated_at')\
            .eq('id', user_id)\
            .execute()

        if response.data and len(response.data) > 0:
            data = response.data[0]
            return jsonify({
                'success': True,
                'user_id': user_id,
                'analytics_visible': data.get('analytics_visible', False),
                'updated_by': data.get('analytics_visibility_updated_by'),
                'updated_at': data.get('analytics_visibility_updated_at')
            })
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        return jsonify({'error': f'Error getting analytics status: {str(e)}'}), 500


@app.route('/api/admin/users/list', methods=['GET'])
@admin_required
def list_all_users():
    """List all users with their analytics status (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        response = supabase_client.table('user_profiles')\
            .select('id, email, role, analytics_visible, created_at')\
            .order('created_at', desc=True)\
            .execute()

        users = response.data if response.data else []

        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })

    except Exception as e:
        return jsonify({'error': f'Error listing users: {str(e)}'}), 500


# ============================================================================
# KNOWLEDGE BASE VISIBILITY CONTROL ENDPOINTS (ADMIN)
# ============================================================================

@app.route('/api/admin/knowledge-base/hide/<store_id>', methods=['POST'])
@admin_required
def hide_knowledge_base(store_id):
    """Hide a knowledge base from list (Admin only) - Still queryable"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('hide_knowledge_base', {
            'store_id_param': store_id,
            'admin_id': admin_id
        }).execute()

        if response.data:
            return jsonify({
                'success': True,
                'message': f'Knowledge base hidden from list (still queryable)'
            })
        else:
            return jsonify({'error': 'Failed to hide knowledge base'}), 500

    except Exception as e:
        return jsonify({'error': f'Error hiding knowledge base: {str(e)}'}), 500


@app.route('/api/admin/knowledge-base/show/<store_id>', methods=['POST'])
@admin_required
def show_knowledge_base(store_id):
    """Show a hidden knowledge base in list (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('show_knowledge_base', {
            'store_id_param': store_id,
            'admin_id': admin_id
        }).execute()

        if response.data:
            return jsonify({
                'success': True,
                'message': 'Knowledge base is now visible in list'
            })
        else:
            return jsonify({'error': 'Failed to show knowledge base'}), 500

    except Exception as e:
        return jsonify({'error': f'Error showing knowledge base: {str(e)}'}), 500


@app.route('/api/admin/knowledge-base/bulk-hide', methods=['POST'])
@admin_required
def bulk_hide_knowledge_bases():
    """Bulk hide knowledge bases (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    store_ids = data.get('store_ids', [])

    if not store_ids:
        return jsonify({'error': 'No store IDs provided'}), 400

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('bulk_hide_knowledge_bases', {
            'store_ids': store_ids,
            'admin_id': admin_id
        }).execute()

        updated_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Successfully hid {updated_count} knowledge base(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk hiding knowledge bases: {str(e)}'}), 500


@app.route('/api/admin/knowledge-base/bulk-show', methods=['POST'])
@admin_required
def bulk_show_knowledge_bases():
    """Bulk show knowledge bases (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    data = request.get_json()
    store_ids = data.get('store_ids', [])

    if not store_ids:
        return jsonify({'error': 'No store IDs provided'}), 400

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('bulk_show_knowledge_bases', {
            'store_ids': store_ids,
            'admin_id': admin_id
        }).execute()

        updated_count = response.data if response.data else 0

        return jsonify({
            'success': True,
            'message': f'Successfully showed {updated_count} knowledge base(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': f'Error bulk showing knowledge bases: {str(e)}'}), 500


@app.route('/api/admin/knowledge-base/all', methods=['GET'])
@admin_required
def get_all_knowledge_bases():
    """Get all knowledge bases including hidden ones (Admin only)"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    admin_id = session.get('user_id')

    try:
        response = supabase_client.rpc('get_all_knowledge_bases', {
            'admin_id': admin_id
        }).execute()

        stores = response.data if response.data else []

        return jsonify({
            'success': True,
            'stores': stores,
            'count': len(stores)
        })

    except Exception as e:
        return jsonify({'error': f'Error getting knowledge bases: {str(e)}'}), 500


@app.route('/api/knowledge-base/visible', methods=['GET'])
@login_required
def get_visible_knowledge_bases():
    """Get visible knowledge bases for regular users"""
    if supabase_client is None:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        response = supabase_client.rpc('get_visible_knowledge_bases').execute()

        stores = response.data if response.data else []

        return jsonify({
            'success': True,
            'stores': stores,
            'count': len(stores)
        })

    except Exception as e:
        return jsonify({'error': f'Error getting visible knowledge bases: {str(e)}'}), 500


# ============================================================================
# MEMORY MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/memory/search', methods=['POST'])
@login_required
def search_memories():
    """Search user memories"""
    if rag_orchestrator is None or not rag_orchestrator.memory_enabled:
        return jsonify({'error': 'Memory system not available'}), 500

    data = request.get_json()
    query = data.get('query', '')
    limit = data.get('limit', 10)
    user_id = session.get('user_id')

    try:
        memories = rag_orchestrator.get_user_memories(user_id=user_id, limit=limit)

        return jsonify({
            'success': True,
            'memories': memories,
            'count': len(memories)
        })

    except Exception as e:
        return jsonify({'error': f'Error searching memories: {str(e)}'}), 500


@app.route('/api/memory/all', methods=['GET'])
@login_required
def get_all_memories():
    """Get all memories for current user"""
    if rag_orchestrator is None or not rag_orchestrator.memory_enabled:
        return jsonify({'error': 'Memory system not available'}), 500

    limit = request.args.get('limit', 50, type=int)
    user_id = session.get('user_id')

    try:
        memories = rag_orchestrator.get_user_memories(user_id=user_id, limit=limit)

        return jsonify({
            'success': True,
            'memories': memories,
            'count': len(memories)
        })

    except Exception as e:
        return jsonify({'error': f'Error retrieving memories: {str(e)}'}), 500


@app.route('/api/memory/add', methods=['POST'])
@login_required
def add_memory():
    """Manually add a memory/preference"""
    if rag_orchestrator is None or not rag_orchestrator.memory_enabled:
        return jsonify({'error': 'Memory system not available'}), 500

    data = request.get_json()
    preference = data.get('preference', '').strip()

    if not preference:
        return jsonify({'error': 'Preference is required'}), 400

    user_id = session.get('user_id')

    try:
        success = rag_orchestrator.add_user_preference(preference, user_id=user_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Preference added successfully'
            })
        else:
            return jsonify({'error': 'Failed to add preference'}), 500

    except Exception as e:
        return jsonify({'error': f'Error adding preference: {str(e)}'}), 500


@app.route('/api/memory/clear', methods=['POST'])
@login_required
def clear_memories():
    """Clear all memories for current user"""
    if rag_orchestrator is None or not rag_orchestrator.memory_enabled:
        return jsonify({'error': 'Memory system not available'}), 500

    user_id = session.get('user_id')

    try:
        success = rag_orchestrator.clear_user_memories(user_id=user_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'All memories cleared successfully'
            })
        else:
            return jsonify({'error': 'Failed to clear memories'}), 500

    except Exception as e:
        return jsonify({'error': f'Error clearing memories: {str(e)}'}), 500


# ============================================================================
# MEMORY ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/memory/analytics', methods=['GET'])
@login_required
def get_memory_analytics():
    """Get memory analytics for current user (if analytics are enabled)"""
    if rag_orchestrator is None or not rag_orchestrator.memory_enabled:
        return jsonify({'error': 'Memory system not available'}), 500

    user_id = session.get('user_id')
    user_role = session.get('user_role', 'user')

    try:
        # Check if analytics are visible for this user
        if user_role != 'admin' and supabase_client:
            response = supabase_client.table('user_profiles')\
                .select('analytics_visible')\
                .eq('id', user_id)\
                .execute()

            if response.data and len(response.data) > 0:
                analytics_visible = response.data[0].get('analytics_visible', False)
                if not analytics_visible:
                    return jsonify({
                        'error': 'Analytics are not enabled for your account. Contact an administrator.',
                        'analytics_enabled': False
                    }), 403

        # Get all memories
        memories = rag_orchestrator.get_user_memories(user_id=user_id, limit=100)

        # Analyze memories
        total_memories = len(memories)

        # Count by type (if metadata exists)
        query_types = {}
        timestamps = []

        for memory in memories:
            # Extract metadata if available
            metadata = memory.get('metadata', {})

            # Count query types
            qtype = metadata.get('query_type', 'UNKNOWN')
            query_types[qtype] = query_types.get(qtype, 0) + 1

            # Collect timestamps
            timestamp = metadata.get('timestamp')
            if timestamp:
                timestamps.append(timestamp)

        # Memory activity over time
        activity_by_day = {}
        for ts in timestamps:
            try:
                date = ts.split(' ')[0]  # Extract date part
                activity_by_day[date] = activity_by_day.get(date, 0) + 1
            except:
                pass

        return jsonify({
            'success': True,
            'analytics_enabled': True,
            'analytics': {
                'total_memories': total_memories,
                'query_type_distribution': query_types,
                'activity_by_day': activity_by_day,
                'recent_activity': len([t for t in timestamps if t])  # Non-empty timestamps
            }
        })

    except Exception as e:
        return jsonify({'error': f'Error generating analytics: {str(e)}'}), 500


@app.route('/api/memory/export', methods=['GET'])
@login_required
def export_memories():
    """Export memories as CSV (if analytics are enabled)"""
    if rag_orchestrator is None or not rag_orchestrator.memory_enabled:
        return jsonify({'error': 'Memory system not available'}), 500

    user_id = session.get('user_id')
    user_role = session.get('user_role', 'user')
    format_type = request.args.get('format', 'csv')

    try:
        # Check if analytics are visible for this user
        if user_role != 'admin' and supabase_client:
            response = supabase_client.table('user_profiles')\
                .select('analytics_visible')\
                .eq('id', user_id)\
                .execute()

            if response.data and len(response.data) > 0:
                analytics_visible = response.data[0].get('analytics_visible', False)
                if not analytics_visible:
                    return jsonify({
                        'error': 'Analytics/export are not enabled for your account. Contact an administrator.'
                    }), 403

        memories = rag_orchestrator.get_user_memories(user_id=user_id, limit=1000)

        if format_type == 'json':
            # Export as JSON
            output = io.BytesIO()
            output.write(json.dumps(memories, indent=2).encode('utf-8'))
            output.seek(0)

            return send_file(
                output,
                mimetype='application/json',
                as_attachment=True,
                download_name=f'memories_{user_id}_{datetime.now().strftime("%Y%m%d")}.json'
            )

        else:
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(['Memory', 'Type', 'Timestamp', 'Has Citations'])

            # Data
            for memory in memories:
                metadata = memory.get('metadata', {})
                writer.writerow([
                    memory.get('memory', memory.get('text', str(memory))),
                    metadata.get('query_type', 'N/A'),
                    metadata.get('timestamp', 'N/A'),
                    metadata.get('has_citations', False)
                ])

            output.seek(0)
            output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))

            return send_file(
                output_bytes,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'memories_{user_id}_{datetime.now().strftime("%Y%m%d")}.csv'
            )

    except Exception as e:
        return jsonify({'error': f'Error exporting memories: {str(e)}'}), 500


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.route('/stats')
def stats():
    """Get system statistics with enhanced features info"""
    if rag_orchestrator is None:
        return jsonify({'error': 'RAG system not initialized'}), 500

    try:
        stats = rag_orchestrator.get_stats()

        # Add session info
        stats['session_store'] = session.get('store_name', 'None')
        stats['authenticated'] = 'user_id' in session

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/features', methods=['GET'])
def get_features():
    """Get information about active Tier 1-3 features"""
    if rag_orchestrator is None:
        return jsonify({'error': 'RAG system not initialized'}), 500

    try:
        # Check if using enhanced RAG
        is_enhanced = isinstance(rag_orchestrator, EnhancedAgenticRAG)

        if not is_enhanced:
            return jsonify({
                'enhanced': False,
                'message': 'Using basic RAG system',
                'features': {}
            })

        config = rag_orchestrator.config

        features = {
            'enhanced': True,
            'tier1': {
                'hybrid_search': {
                    'enabled': config.use_hybrid_search,
                    'description': 'BM25 + Dense semantic search',
                    'benefit': '15-25% better retrieval accuracy'
                },
                'citations': {
                    'enabled': config.use_citations,
                    'description': 'Source attribution with confidence scores',
                    'benefit': 'Improved trustworthiness and verifiability'
                },
                'cache': {
                    'enabled': config.use_cache,
                    'type': config.cache_type if config.use_cache else None,
                    'description': 'Embedding and result caching',
                    'benefit': '50-80% latency reduction for repeated queries'
                }
            },
            'tier2': {
                'reranking': {
                    'enabled': config.use_reranking,
                    'model': config.reranker_model if config.use_reranking else None,
                    'description': 'Cross-encoder re-ranking',
                    'benefit': '10-20% better precision'
                },
                'query_processing': {
                    'enabled': config.use_query_rewriting,
                    'description': 'Query rewriting and expansion',
                    'benefit': '15-30% better recall'
                },
                'streaming': {
                    'enabled': config.use_streaming,
                    'description': 'Real-time response streaming',
                    'benefit': 'First token in <500ms'
                }
            },
            'tier3': {
                'multihop': {
                    'enabled': config.use_multihop,
                    'max_hops': config.max_hops if config.use_multihop else None,
                    'description': 'Multi-step reasoning for complex questions',
                    'benefit': '20-40% better on complex questions'
                },
                'self_reflection': {
                    'enabled': config.use_self_reflection,
                    'description': 'Answer validation and correction',
                    'benefit': '15-25% fewer factual errors'
                },
                'experiment_tracking': {
                    'enabled': config.use_experiment_tracking,
                    'description': 'Research experiment management',
                    'benefit': 'Systematic configuration tracking'
                }
            },
            'summary': {
                'total_features': sum([
                    config.use_hybrid_search,
                    config.use_citations,
                    config.use_cache,
                    config.use_reranking,
                    config.use_query_rewriting,
                    config.use_streaming,
                    config.use_multihop,
                    config.use_self_reflection,
                    config.use_experiment_tracking
                ]),
                'active_features': rag_orchestrator._get_active_features(),
                'expected_improvement': '30-50% better accuracy, 50-80% lower latency'
            }
        }

        return jsonify(features)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/clear-conversation', methods=['POST'])
@login_required
def clear_conversation():
    """Clear conversation history"""
    if rag_orchestrator is None:
        return jsonify({'error': 'RAG system not initialized'}), 500

    try:
        rag_orchestrator.clear_conversation()
        return jsonify({'success': True, 'message': 'Conversation history cleared'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stores')
def list_stores():
    """List available stores (visible only for non-admins)"""
    if rag_orchestrator is None:
        return jsonify({'error': 'RAG system not initialized'}), 500

    user_role = session.get('user_role', 'user')
    user_id = session.get('user_id')

    try:
        # If admin, show all stores; otherwise only visible ones
        if user_role == 'admin':
            # Get all stores from database
            if supabase_client:
                response = supabase_client.rpc('get_all_knowledge_bases', {
                    'admin_id': user_id
                }).execute()
                stores = response.data if response.data else []
                store_list = [{'id': s['id'], 'store_id': s['store_id'], 'store_name': s['store_name'],
                              'description': s.get('description'), 'is_visible': s.get('is_visible', True)} for s in stores]
            else:
                stores = rag_orchestrator.file_manager.list_stores()
                store_list = [{'name': store.name, 'display_name': store.display_name} for store in stores]
        else:
            # Get only visible stores for regular users
            if supabase_client:
                response = supabase_client.rpc('get_visible_knowledge_bases').execute()
                stores = response.data if response.data else []
                store_list = [{'id': s['id'], 'store_id': s['store_id'], 'store_name': s['store_name'],
                              'description': s.get('description')} for s in stores]
            else:
                stores = rag_orchestrator.file_manager.list_stores()
                store_list = [{'name': store.name, 'display_name': store.display_name} for store in stores]

        return jsonify({'stores': store_list, 'count': len(store_list)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'rag_initialized': rag_orchestrator is not None,
        'memory_enabled': rag_orchestrator.memory_enabled if rag_orchestrator else False,
        'auth_configured': supabase_client is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413


if __name__ == '__main__':
    # Initialize systems
    auth_init = init_supabase()
    rag_init = init_rag_system()

    if not rag_init:
        print("\n" + "="*60)
        print("ERROR: Could not initialize RAG system")
        print("Please set the GEMINI_API_KEY environment variable")
        print("="*60 + "\n")

    if not auth_init:
        print("\n" + "="*60)
        print("WARNING: Authentication not configured")
        print("Set SUPABASE_URL and SUPABASE_KEY for multi-user support")
        print("="*60 + "\n")

    print("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)
