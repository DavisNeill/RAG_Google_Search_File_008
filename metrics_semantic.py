"""
Semantic Similarity Metrics Module
===================================

Implements semantic similarity metrics for evaluating answer quality:
- BERTScore: Semantic similarity using BERT embeddings (SOTA)
- ROUGE-L: Longest common subsequence
- BLEU: N-gram overlap (traditional)

These metrics evaluate semantic similarity between generated and reference answers.
"""

from typing import List, Dict, Any
import numpy as np

try:
    from bert_score import score as bert_score_fn
    BERTSCORE_AVAILABLE = True
except ImportError:
    print("Warning: BERTScore not installed. Install with: pip install bert-score")
    BERTSCORE_AVAILABLE = False

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    print("Warning: ROUGE not installed. Install with: pip install rouge-score")
    ROUGE_AVAILABLE = False

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
    # Download required data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    BLEU_AVAILABLE = True
except ImportError:
    print("Warning: NLTK not installed. Install with: pip install nltk")
    BLEU_AVAILABLE = False


class SemanticEvaluator:
    """
    Evaluator for semantic similarity metrics

    Uses state-of-the-art methods to measure semantic similarity
    between generated and reference answers.
    """

    def __init__(self, use_bertscore: bool = True, use_rouge: bool = True, use_bleu: bool = True):
        """
        Initialize semantic evaluator

        Args:
            use_bertscore: Whether to compute BERTScore
            use_rouge: Whether to compute ROUGE
            use_bleu: Whether to compute BLEU
        """
        self.use_bertscore = use_bertscore and BERTSCORE_AVAILABLE
        self.use_rouge = use_rouge and ROUGE_AVAILABLE
        self.use_bleu = use_bleu and BLEU_AVAILABLE

        if self.use_rouge:
            self.rouge_scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

        print(f"[Semantic Evaluator] Initialized")
        print(f"  BERTScore: {'✓' if self.use_bertscore else '✗'}")
        print(f"  ROUGE: {'✓' if self.use_rouge else '✗'}")
        print(f"  BLEU: {'✓' if self.use_bleu else '✗'}")

    def evaluate_batch(self, results: List[Any]) -> Dict[str, float]:
        """
        Evaluate semantic metrics on a batch of results

        Args:
            results: List of QueryResult objects

        Returns:
            Dictionary of aggregated semantic metrics
        """
        predictions = [r.predicted_answer for r in results]
        references = [r.ground_truth for r in results]

        metrics = {}

        # BERTScore
        if self.use_bertscore:
            print("  Computing BERTScore...")
            bertscore_metrics = self.compute_bertscore_batch(predictions, references)
            metrics.update(bertscore_metrics)

        # ROUGE
        if self.use_rouge:
            print("  Computing ROUGE...")
            rouge_metrics = self.compute_rouge_batch(predictions, references)
            metrics.update(rouge_metrics)

        # BLEU
        if self.use_bleu:
            print("  Computing BLEU...")
            bleu_metrics = self.compute_bleu_batch(predictions, references)
            metrics.update(bleu_metrics)

        return metrics

    def compute_bertscore_batch(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """
        Compute BERTScore for a batch

        BERTScore computes semantic similarity using BERT embeddings.
        Widely accepted in NLP research (cited 1000+ times).

        Args:
            predictions: List of predicted answers
            references: List of reference answers

        Returns:
            Dictionary with BERTScore metrics (Precision, Recall, F1)
        """
        if not BERTSCORE_AVAILABLE:
            return {}

        # Compute BERTScore
        P, R, F1 = bert_score_fn(
            predictions,
            references,
            lang="en",
            verbose=False,
            device='cpu'  # Use 'cuda' if GPU available
        )

        return {
            'bertscore_precision': float(P.mean()),
            'bertscore_recall': float(R.mean()),
            'bertscore_f1': float(F1.mean())
        }

    def compute_rouge_batch(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """
        Compute ROUGE-L for a batch

        ROUGE-L measures longest common subsequence.
        Standard metric in summarization and QA tasks.

        Args:
            predictions: List of predicted answers
            references: List of reference answers

        Returns:
            Dictionary with ROUGE-L metrics (Precision, Recall, F1)
        """
        if not ROUGE_AVAILABLE:
            return {}

        scores = []
        for pred, ref in zip(predictions, references):
            score = self.rouge_scorer.score(ref, pred)
            scores.append(score['rougeL'])

        # Average scores
        precision = np.mean([s.precision for s in scores])
        recall = np.mean([s.recall for s in scores])
        f1 = np.mean([s.fmeasure for s in scores])

        return {
            'rouge_l_precision': float(precision),
            'rouge_l_recall': float(recall),
            'rouge_l_f1': float(f1)
        }

    def compute_bleu_batch(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """
        Compute BLEU for a batch

        BLEU measures n-gram overlap between prediction and reference.
        Traditional metric from machine translation.

        Args:
            predictions: List of predicted answers
            references: List of reference answers

        Returns:
            Dictionary with BLEU scores (BLEU-1, BLEU-2, BLEU-3, BLEU-4)
        """
        if not BLEU_AVAILABLE:
            return {}

        smoothing = SmoothingFunction().method1
        bleu_scores = {
            'bleu_1': [],
            'bleu_2': [],
            'bleu_3': [],
            'bleu_4': []
        }

        for pred, ref in zip(predictions, references):
            pred_tokens = pred.split()
            ref_tokens = [ref.split()]

            # Compute BLEU with different n-gram weights
            bleu_1 = sentence_bleu(ref_tokens, pred_tokens, weights=(1, 0, 0, 0), smoothing_function=smoothing)
            bleu_2 = sentence_bleu(ref_tokens, pred_tokens, weights=(0.5, 0.5, 0, 0), smoothing_function=smoothing)
            bleu_3 = sentence_bleu(ref_tokens, pred_tokens, weights=(0.33, 0.33, 0.33, 0), smoothing_function=smoothing)
            bleu_4 = sentence_bleu(ref_tokens, pred_tokens, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=smoothing)

            bleu_scores['bleu_1'].append(bleu_1)
            bleu_scores['bleu_2'].append(bleu_2)
            bleu_scores['bleu_3'].append(bleu_3)
            bleu_scores['bleu_4'].append(bleu_4)

        # Average scores
        return {
            'bleu_1': float(np.mean(bleu_scores['bleu_1'])),
            'bleu_2': float(np.mean(bleu_scores['bleu_2'])),
            'bleu_3': float(np.mean(bleu_scores['bleu_3'])),
            'bleu_4': float(np.mean(bleu_scores['bleu_4']))
        }

    def compute_single(
        self,
        prediction: str,
        reference: str
    ) -> Dict[str, float]:
        """
        Compute semantic metrics for a single prediction-reference pair

        Args:
            prediction: Predicted answer
            reference: Reference answer

        Returns:
            Dictionary of semantic similarity scores
        """
        metrics = {}

        # BERTScore
        if self.use_bertscore:
            P, R, F1 = bert_score_fn([prediction], [reference], lang="en", verbose=False)
            metrics['bertscore_f1'] = float(F1[0])

        # ROUGE
        if self.use_rouge:
            score = self.rouge_scorer.score(reference, prediction)
            metrics['rouge_l_f1'] = float(score['rougeL'].fmeasure)

        # BLEU
        if self.use_bleu:
            pred_tokens = prediction.split()
            ref_tokens = [reference.split()]
            smoothing = SmoothingFunction().method1
            bleu = sentence_bleu(ref_tokens, pred_tokens, smoothing_function=smoothing)
            metrics['bleu_4'] = float(bleu)

        return metrics


if __name__ == "__main__":
    print("Semantic Similarity Metrics Evaluator")
    print("=" * 60)

    evaluator = SemanticEvaluator()

    # Example usage
    print("\nExample Evaluation:")
    prediction = "Machine learning is a branch of artificial intelligence that enables computers to learn from data."
    reference = "Machine learning is a subset of AI that allows systems to learn from data without explicit programming."

    print(f"\nPrediction: {prediction}")
    print(f"Reference: {reference}")

    scores = evaluator.compute_single(prediction, reference)

    print("\nSemantic Similarity Scores:")
    for metric_name, value in sorted(scores.items()):
        print(f"  {metric_name}: {value:.4f}")

    print("\nInterpretation:")
    print("  - BERTScore F1 > 0.9: Excellent semantic match")
    print("  - BERTScore F1 > 0.8: Good semantic match")
    print("  - BERTScore F1 > 0.7: Moderate semantic match")
    print("  - ROUGE-L F1 > 0.5: Good lexical overlap")
    print("  - BLEU-4 > 0.3: Good n-gram overlap")
