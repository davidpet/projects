"""Utilities for doing error analysis on model predictionss."""

import tensorflow as tf

from machine_learning.common import visualization


# TODO: Maybe add tests for the reshaping since I already had a bug there.
def compute_error_analysis_matrices(
        data: tf.Tensor, labels: tf.Tensor,
        predictions: tf.Tensor) -> dict[str, tf.Tensor]:
    """
    Compute the 4 error analysis matrices based on label and predictions.

    Args:
        data (tf.Tensor): The unbatched input data that will be sliced
            according to the values of labels and predictions.
        labels (tf.Tensor): The labels for dataset samples.  Shape is
            (num_samples) (will get reshaped). Values should be 0 or 1.
        predictions (tf.Tensor): The actual output from the model.
            Shape can be (num_samples) or whatever TF returns (will
            get reshaped).  Values should be 0 or 1.
    Returns:
        Dictionary of 4 tensors.  Keys are true_positives,
        true_negatives, false_positives, and false_negatives.

        Missing ones will have shape (0, num_features).
    """
    reshaped_labels = tf.reshape(labels, (-1))
    reshaped_predictions = tf.reshape(predictions, (-1))
    true_mask = reshaped_labels == reshaped_predictions
    positive_mask = reshaped_predictions == 1

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


def print_error_analysis_matrices(matrices: dict[str, tf.Tensor]) -> None:
    """Print dictionary of tensorflow tensors showing their keys as titles."""

    for title in matrices:
        print(f'[{title}]')
        print(f'Shape: {matrices[title].shape}')
        print()
        visualization.print_matrix(matrices[title])
        print('--------------------------')
        print()
