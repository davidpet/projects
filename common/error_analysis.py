import tensorflow as tf
from typing import Dict
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import visualization

#import importlib
#importlib.reload(visualization)

def compute_error_analysis_matrices(data: tf.Tensor, labels: tf.Tensor, predictions: tf.Tensor) -> Dict[str, tf.Tensor]:
    """Compute the 4 error analysis matrices based on label and predictions.

    Args:
        data (tf.Tensor): The input data that will be sliced according to the values of labels and predictions.
        labels (tf.Tensor): The labels for dataset samples.  Shape is (num_samples). Values should be 0 or 1.
        predictions (tf.Tensor): The actual output from the model. Shape can be (num_samples) or whatever TF returns (will get reshaped).  Values should be 0 or 1.
    Returns:
        Dictionary of 4 tensors.  Keys are true_positives, true_negatives, false_positives, and false_negatives.
    """
    true_mask = labels == tf.reshape(predictions, (-1,))
    positive_mask = labels == 1

    tp_mask = true_mask & positive_mask
    tn_mask = true_mask & ~positive_mask
    fp_mask = ~true_mask & positive_mask
    fn_mask = ~true_mask & ~positive_mask

    return {
        'true_positives': data[tp_mask],
        'true_negatives': data[tn_mask],
        'false_positives': data[fp_mask],
        'false_negatives': data[fn_mask],
    }

def print_error_analysis_matrices(matrices: dict) -> None:
    """Print dictionary of tensorflow tensors showing their keys as titles.
    """

    for title in matrices:
        print(f'[{title}]')
        print(f'Shape: {matrices[title].shape}')
        print()
        visualization.print_matrix(matrices[title])
        print('--------------------------')
        print()
