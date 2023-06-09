"""Utilities for visualizing and plotting data."""

import matplotlib.pyplot as plt
import pandas as pd
import tensorflow as tf
import numpy as np


def examine_candidate_column(dataframe: pd.DataFrame,
                             candidate_column: str,
                             candidate_display_name: str,
                             label_column: str,
                             label_display_name: str,
                             test_series_fn=None) -> None:
    """
    Plot a graph of % of label true for values of a candidate column using
    matplotlib.

    Args:
        dataframe (pd.DataFrame): The dataframe containing the columns.
        candidate_column (str): The column name being examined.
        candidate_display_name (str): Display name for candidate column
            in the plot.
        label_column (str): The target value (y-axis) - assumed to be 0 or 1.
        label_display_name (str): Display name for label column in the plot.
        test_series_fn: For testing only - a function that will be called with
            the pd.Series object that will be plotted. (needed because mocking
            inaccessible instance methods not working)

    Returns:
        None
    """

    series = dataframe.groupby(candidate_column)[label_column].mean() * 100
    if test_series_fn:
        test_series_fn(series)

    ax = series.plot(kind='bar')
    ax.set_xlabel(f'{candidate_display_name} ({candidate_column})')
    ax.set_ylabel(f'% {label_display_name}')

    plt.xticks(rotation=0)
    plt.show()


def compute_truth_ratio(dataframe: pd.DataFrame, label_column: str) -> float:
    """
    Get the ratio of rows in a dataframe that have a true label value.  If not
    50%, the dataset is skewed.

    Args:
        dataframe (pd.DataFrame): The dataframe containing the data.
        label_column (str): The column to use as the label (assumed to contain
            0 or 1).

    Returns:
        float: The ratio of rows that have true (1) labels.
    """

    num_true = len(dataframe[dataframe[label_column] != 0])
    return num_true / len(dataframe)


# TODO: Handle lack of val_accuracy field in history if that ever comes up
def graph_training_stats(history) -> None:
    """
    Plot the training loss and accuracy per epoch from the return value of
    model.fit.
    """

    plt.figure(figsize=(10, 12))

    plt.subplot(2, 2, 1)
    plt.plot(history.history['loss'])
    plt.title('Loss')
    plt.xlabel('Epoch')

    plt.subplot(2, 2, 2)
    plt.plot(history.history['accuracy'])
    plt.title('Accuracy')
    plt.xlabel('Epoch')
    plt.yticks([0.25, 0.5, 0.75, 1], ['25%', '50%', '75%', '100%'])

    plt.subplot(2, 2, 3)
    plt.plot(history.history['val_accuracy'])
    plt.title('Validation Accuracy')
    plt.xlabel('Epoch')
    plt.yticks([0.25, 0.5, 0.75, 1], ['25%', '50%', '75%', '100%'])

    plt.tight_layout()
    plt.show()


def print_matrix(matrix: tf.Tensor | np.ndarray) -> None:
    """
    Print the columns of a tensor/matrix with tabs in between,
    1 sample per line.
    """

    if isinstance(matrix, tf.Tensor):
        np_matrix = matrix.numpy()
    else:
        np_matrix = matrix

    if len(np_matrix.shape) == 0:
        print()
        return

    for i in range(np_matrix.shape[0]):
        for j in range(np_matrix.shape[1]):
            print(np_matrix[i][j], end='\t')
        print()
