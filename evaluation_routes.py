"""
Evaluation Dashboard Routes
============================

Flask routes for the research evaluation dashboard.
Provides API endpoints and pages for viewing and managing evaluation results.
"""

from flask import Blueprint, render_template, request, jsonify, session, send_file
from functools import wraps
import json
from datetime import datetime, timedelta
from pathlib import Path
import io

from evaluation_db import EvaluationDB


# Create blueprint
evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        if not session.get('is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function


def get_eval_db():
    """Get evaluation database instance"""
    from flask import current_app
    supabase_client = current_app.config.get('SUPABASE_CLIENT')
    if not supabase_client:
        return None
    return EvaluationDB(supabase_client)


# ==================== Dashboard Pages ====================

@evaluation_bp.route('/dashboard')
@admin_required
def dashboard():
    """Main evaluation dashboard page"""
    return render_template('evaluation_dashboard.html')


@evaluation_bp.route('/runs')
@admin_required
def evaluation_runs():
    """Evaluation runs history page"""
    return render_template('evaluation_runs.html')


@evaluation_bp.route('/runs/<evaluation_id>')
@admin_required
def evaluation_detail(evaluation_id):
    """Detailed view of a single evaluation"""
    return render_template('evaluation_detail.html', evaluation_id=evaluation_id)


@evaluation_bp.route('/datasets')
@admin_required
def datasets():
    """Evaluation datasets management page"""
    return render_template('evaluation_datasets.html')


# ==================== API Endpoints ====================

# Dashboard Stats
@evaluation_bp.route('/api/stats')
@admin_required
def get_dashboard_stats():
    """Get overall dashboard statistics"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        stats = eval_db.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Recent Evaluations
@evaluation_bp.route('/api/recent')
@admin_required
def get_recent_evaluations():
    """Get recent evaluation runs"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    limit = request.args.get('limit', 10, type=int)

    try:
        evaluations = eval_db.get_recent_evaluations(limit=limit)
        return jsonify({'evaluations': evaluations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Evaluation Details
@evaluation_bp.route('/api/runs/<evaluation_id>')
@admin_required
def get_evaluation_details(evaluation_id):
    """Get complete details for an evaluation run"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        # Get evaluation run
        run = eval_db.get_evaluation_run(evaluation_id)
        if not run:
            return jsonify({'error': 'Evaluation not found'}), 404

        # Get detailed metrics
        metrics = eval_db.get_evaluation_metrics(evaluation_id)

        # Get baseline comparisons
        baselines = eval_db.get_baseline_comparisons(evaluation_id)

        # Get ablation results
        ablations = eval_db.get_ablation_results(evaluation_id)

        # Get statistical tests
        stats_tests = eval_db.get_statistical_tests(evaluation_id)

        # Get error summary
        error_summary = eval_db.get_error_summary(evaluation_id)

        # Get query type performance
        query_types = eval_db.get_query_type_performance(evaluation_id)

        # Get efficiency metrics
        efficiency = eval_db.get_efficiency_metrics(evaluation_id)

        return jsonify({
            'run': run,
            'metrics': metrics,
            'baselines': baselines,
            'ablations': ablations,
            'statistical_tests': stats_tests,
            'error_summary': error_summary,
            'query_type_performance': query_types,
            'efficiency': efficiency
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Metrics Over Time
@evaluation_bp.route('/api/trends')
@admin_required
def get_performance_trends():
    """Get performance trends over time"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    days = request.args.get('days', 30, type=int)

    try:
        trends = eval_db.get_performance_trends(days=days)
        return jsonify({'trends': trends})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Performance Improvement
@evaluation_bp.route('/api/improvement')
@admin_required
def get_performance_improvement():
    """Calculate performance improvement over time"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    days = request.args.get('days', 30, type=int)

    try:
        improvement = eval_db.get_performance_improvement(days=days)
        return jsonify({'improvement': improvement})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Baseline Comparisons
@evaluation_bp.route('/api/runs/<evaluation_id>/baselines')
@admin_required
def get_baseline_comparisons(evaluation_id):
    """Get baseline comparisons for an evaluation"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        baselines = eval_db.get_baseline_comparisons(evaluation_id)
        return jsonify({'baselines': baselines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Ablation Studies
@evaluation_bp.route('/api/runs/<evaluation_id>/ablations')
@admin_required
def get_ablation_studies(evaluation_id):
    """Get ablation study results"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        ablations = eval_db.get_ablation_results(evaluation_id)
        return jsonify({'ablations': ablations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Error Analysis
@evaluation_bp.route('/api/runs/<evaluation_id>/errors')
@admin_required
def get_error_analysis(evaluation_id):
    """Get error analysis for an evaluation"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    error_type = request.args.get('type')
    severity = request.args.get('severity')

    try:
        errors = eval_db.get_error_cases(
            evaluation_id,
            error_type=error_type,
            error_severity=severity
        )
        summary = eval_db.get_error_summary(evaluation_id)

        return jsonify({
            'errors': errors,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Query Type Performance
@evaluation_bp.route('/api/runs/<evaluation_id>/query-types')
@admin_required
def get_query_type_performance(evaluation_id):
    """Get query type performance breakdown"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        query_types = eval_db.get_query_type_performance(evaluation_id)
        return jsonify({'query_types': query_types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Efficiency Metrics
@evaluation_bp.route('/api/runs/<evaluation_id>/efficiency')
@admin_required
def get_efficiency_metrics(evaluation_id):
    """Get efficiency metrics"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        efficiency = eval_db.get_efficiency_metrics(evaluation_id)
        return jsonify(efficiency if efficiency else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Statistical Tests
@evaluation_bp.route('/api/runs/<evaluation_id>/statistical-tests')
@admin_required
def get_statistical_tests(evaluation_id):
    """Get statistical significance test results"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        tests = eval_db.get_statistical_tests(evaluation_id)
        return jsonify({'tests': tests})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Run New Evaluation ====================

@evaluation_bp.route('/api/run', methods=['POST'])
@admin_required
def run_new_evaluation():
    """Trigger a new evaluation run"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    experiment_name = data.get('experiment_name')
    dataset_name = data.get('dataset_name')

    if not experiment_name:
        return jsonify({'error': 'Experiment name required'}), 400

    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        # Create evaluation run
        run = eval_db.create_evaluation_run(
            experiment_name=experiment_name,
            created_by=session.get('user_id'),
            dataset_name=dataset_name,
            metadata=data.get('metadata', {})
        )

        # TODO: Actually run evaluation in background task
        # For now, just return the created run
        # In production, use Celery or similar for background processing

        return jsonify({
            'success': True,
            'evaluation_id': run['id'],
            'message': 'Evaluation started',
            'run': run
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Export Functions ====================

@evaluation_bp.route('/api/runs/<evaluation_id>/export/latex')
@admin_required
def export_latex(evaluation_id):
    """Export LaTeX tables for an evaluation"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        # Get evaluation data
        run = eval_db.get_evaluation_run(evaluation_id)
        if not run:
            return jsonify({'error': 'Evaluation not found'}), 404

        metrics = eval_db.get_evaluation_metrics(evaluation_id)
        baselines = eval_db.get_baseline_comparisons(evaluation_id)
        ablations = eval_db.get_ablation_results(evaluation_id)

        # Generate LaTeX using latex_export module
        from latex_export import LaTeXExporter

        exporter = LaTeXExporter(output_dir='/tmp/latex_export')

        # Generate all tables
        # (Implementation depends on data structure)

        # For now, return a placeholder
        latex_content = f"""
% Evaluation Results: {run['experiment_name']}
% Generated: {datetime.now().isoformat()}

\\section{{Evaluation Results}}

% TODO: Generate actual LaTeX tables from data
"""

        # Save export record
        export_path = f"/tmp/latex_export/{evaluation_id}_tables.tex"
        eval_db.save_export(
            evaluation_id=evaluation_id,
            export_type='latex',
            export_name=f"{run['experiment_name']}_tables",
            file_path=export_path,
            file_size=len(latex_content),
            exported_by=session.get('user_id')
        )

        # Return as downloadable file
        return send_file(
            io.BytesIO(latex_content.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{run['experiment_name']}_tables.tex"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/api/runs/<evaluation_id>/export/json')
@admin_required
def export_json(evaluation_id):
    """Export complete evaluation data as JSON"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        # Get all evaluation data
        run = eval_db.get_evaluation_run(evaluation_id)
        if not run:
            return jsonify({'error': 'Evaluation not found'}), 404

        data = {
            'run': run,
            'metrics': eval_db.get_evaluation_metrics(evaluation_id),
            'baselines': eval_db.get_baseline_comparisons(evaluation_id),
            'ablations': eval_db.get_ablation_results(evaluation_id),
            'statistical_tests': eval_db.get_statistical_tests(evaluation_id),
            'query_type_performance': eval_db.get_query_type_performance(evaluation_id),
            'efficiency': eval_db.get_efficiency_metrics(evaluation_id),
            'error_summary': eval_db.get_error_summary(evaluation_id)
        }

        json_content = json.dumps(data, indent=2, default=str)

        # Save export record
        eval_db.save_export(
            evaluation_id=evaluation_id,
            export_type='json',
            export_name=f"{run['experiment_name']}_data",
            file_path=f"/tmp/{evaluation_id}_data.json",
            file_size=len(json_content),
            exported_by=session.get('user_id')
        )

        # Return as downloadable file
        return send_file(
            io.BytesIO(json_content.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f"{run['experiment_name']}_data.json"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Delete Evaluation ====================

@evaluation_bp.route('/api/runs/<evaluation_id>', methods=['DELETE'])
@admin_required
def delete_evaluation(evaluation_id):
    """Delete an evaluation run and all associated data"""
    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        # Delete from database (CASCADE will delete related records)
        eval_db.client.table('evaluation_runs')\
            .delete()\
            .eq('id', evaluation_id)\
            .execute()

        return jsonify({'success': True, 'message': 'Evaluation deleted'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Compare Evaluations ====================

@evaluation_bp.route('/api/compare')
@admin_required
def compare_evaluations():
    """Compare multiple evaluation runs"""
    eval_ids = request.args.getlist('ids')

    if not eval_ids or len(eval_ids) < 2:
        return jsonify({'error': 'At least 2 evaluation IDs required'}), 400

    eval_db = get_eval_db()
    if not eval_db:
        return jsonify({'error': 'Database not configured'}), 500

    try:
        comparisons = []

        for eval_id in eval_ids:
            run = eval_db.get_evaluation_run(eval_id)
            metrics = eval_db.get_evaluation_metrics(eval_id)

            if run and metrics:
                comparisons.append({
                    'id': eval_id,
                    'name': run['experiment_name'],
                    'created_at': run['created_at'],
                    'overall_score': run['overall_score'],
                    'ragas_score': run['ragas_score'],
                    'ir_score': run['ir_score'],
                    'semantic_score': run['semantic_score'],
                    'metrics': metrics
                })

        return jsonify({'comparisons': comparisons})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    print("Evaluation Dashboard Routes")
    print("=" * 60)
    print("\nAvailable Routes:")
    print("Pages:")
    print("  GET  /evaluation/dashboard")
    print("  GET  /evaluation/runs")
    print("  GET  /evaluation/runs/<id>")
    print("  GET  /evaluation/datasets")
    print("\nAPI Endpoints:")
    print("  GET  /evaluation/api/stats")
    print("  GET  /evaluation/api/recent")
    print("  GET  /evaluation/api/trends")
    print("  GET  /evaluation/api/runs/<id>")
    print("  GET  /evaluation/api/runs/<id>/baselines")
    print("  GET  /evaluation/api/runs/<id>/ablations")
    print("  GET  /evaluation/api/runs/<id>/errors")
    print("  GET  /evaluation/api/runs/<id>/query-types")
    print("  GET  /evaluation/api/runs/<id>/efficiency")
    print("  GET  /evaluation/api/runs/<id>/statistical-tests")
    print("  POST /evaluation/api/run")
    print("  GET  /evaluation/api/runs/<id>/export/latex")
    print("  GET  /evaluation/api/runs/<id>/export/json")
    print("  DEL  /evaluation/api/runs/<id>")
    print("  GET  /evaluation/api/compare")
