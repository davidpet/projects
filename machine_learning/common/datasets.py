"""Utilities for dealing with Tensorflow datasets."""

import tensorflow as tf
import math
from typing import Tuple
from sklearn.preprocessing import StandardScaler


@tf.autograph.experimental.do_not_convert
def count_batches(dataset: tf.data.Dataset) -> int:
    """
    Count the number of batches in a dataset by reading through all of them.

    Args:
        dataset (tf.data.Dataset): The dataset.

    Returns:
        (int): The count.
    """

    return dataset.reduce(0, lambda x, _: x + 1)


def get_first_batch(dataset: tf.data.Dataset):
    """
    Get the first batch of the dataset.

    All tensors are converted to numpy equivalents.

    TODO: Consider not doing that (then need to update places using this)

    Args:
        dataset (tf.data.Dataset): The dataset.

    Returns:
        The first batch (whose type can vary).
        None if empty dataset.
    """

    try:
        return next(dataset.take(1).as_numpy_iterator())
    except StopIteration:
        return None


def show_first_batch(dataset: tf.data.Dataset) -> None:
    """
    Print the first batch of the dataset in a way that depends on types.

    Args:
        dataset (tf.data.Dataset): The dataset.

    Returns:
        None
    """

    batch = get_first_batch(dataset)

    def print_inner_batch(batch):
        if isinstance(batch, dict):
            print(dict(batch))
        else:
            print(batch)

    if isinstance(batch, tuple):
        print('---Features---')
        print_inner_batch(batch[0])
        print('---Labels---')
        print(batch[1])
    else:
        print_inner_batch(batch)


def split(
        dataset: tf.data.Dataset,
        num_batches: float,
        training_ratio: float = 0.8) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
    """
    Split a dataset into a training and validation set.

    Args:
        dataset (tf.data.Dataset): The dataset.
        num_batches(float): The total number of batches in the dataset
            (can be complete or partial).
        training_ratio(float): The ratio of training batches to total batches.

    Returns:
        Tuple of (training, validation) datasets with training containing the
        first batches rounded down from applying the ratio.
    """

    training_batches = int(math.floor(num_batches * training_ratio))

    return (dataset.take(training_batches), dataset.skip(training_batches))


def safe_batch_transformer(transform_fn):
    """ 
    Get a function (for use in dataset.map) that preserves the label part
    (if applicable) and transforms the data part. 
    """

    def wrapper_fn(batch, labels=None):
        new_batch = transform_fn(batch)
        if labels is None:
            return new_batch
        else:
            return (new_batch, labels)

    return wrapper_fn


def named_column_scaler(scalers: dict):
    """
    Get a function that can be passed into dataset.map() to apply scalers
    to columns in a batch dictionary.
    """

    def batch_column_scaler(batch: dict):
        new_batch = {}

        # This needs to be a function to capture feature_name by value in the
        # loop below. Otherwise, really weird things happen
        # with tf.numpy_function.
        def scale_column(feature_vector, feature_name):
            # Need to use tf.numpy_function because we need to make
            # feature_vector a numpy vector for StandardScaler.
            return tf.numpy_function(scalers[feature_name].transform,
                                     [feature_vector], tf.double)

        for feature_name in batch:
            feature_value = batch[feature_name]
            if feature_name in scalers:
                feature_col_vector = tf.reshape(feature_value, (-1, 1))
                scaled_feature_col_vector = scale_column(
                    feature_col_vector, feature_name)
                new_batch[feature_name] = tf.reshape(scaled_feature_col_vector,
                                                     (-1,))
            else:
                new_batch[feature_name] = feature_value

        return new_batch

    return safe_batch_transformer(batch_column_scaler)


# TODO: Multi-column version of this (using this) to pass into map()
def remap_column_entries(column_values, value_mappings):
    """
    Take in a tf vector of values and transform it using value_mappings
    dictionary (eg. for categories to numbers).
    
    For now, you can only map TO an integer value.

    TODO: maybe fix that eventually if needed as it was not intentional
    (though might still make sense).
    """

    keys = list(value_mappings.keys())
    values = [value_mappings[k] for k in keys]
    table = tf.lookup.StaticHashTable(
        tf.lookup.KeyValueTensorInitializer(keys, values), -1)

    return table.lookup(column_values)


def named_column_oh_expander(one_hot_specs: dict):
    """
    Get a function that can be passed into dataset.map() to expand given
    columns w/ given # categories into one-hot vectors.
    
    Right now, only dictionary datasets are supported
    TODO: expand support to tensor datasets

    Negative numbers will become all zero vectors, as that is what
    TF does with them.
    """

    def batch_expander(batch: dict):
        new_batch = {}

        for feature in batch:
            feature_value = batch[feature]
            if feature in one_hot_specs:
                new_batch[feature] = tf.one_hot(feature_value,
                                                one_hot_specs[feature])
            else:
                new_batch[feature] = feature_value

        return new_batch

    return safe_batch_transformer(batch_expander)


def create_named_scalers(column_names: list) -> dict:
    """
    Create default feature scalers as dictionary of column name to new scaler.
    """

    return {name: StandardScaler() for name in column_names}


# TODO: consider index version
# TODO: consider multiple columns at once version since StandardScaler
#       supports it
def train_named_scalers(scalers: dict, dataset: tf.data.Dataset) -> None:
    """
    Train dictionary of scalers (as returned by create_scalers) based on
    dictionary dataset.
    """

    for element in dataset:
        if isinstance(element, tuple):
            batch, _ = element
        else:
            batch = element
        for column_name in scalers:
            scalers[column_name].partial_fit(
                tf.reshape(batch[column_name], (-1, 1)).numpy())


def to_matrix(dtype=tf.float32):
    """
    Get a function that can be passed into dataset.map() to turn a dictionary
    dataset into a tensor dataset.
    
    The order of columns will match the order of dictionary keys.  Elements
    will be cast to make them compatible.
    """

    def batch_to_matrix(batch_dict):
        raw_tensors = list(batch_dict.values())
        reshaped_tensors = list(
            map(lambda x: tf.expand_dims(x, axis=1)
                if x.shape.rank == 1 else x, raw_tensors))
        compatible_tensors = list(
            map(lambda x: tf.cast(x, dtype), reshaped_tensors))

        return tf.concat(compatible_tensors, axis=1)  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter

    return safe_batch_transformer(batch_to_matrix)


def collect_tensors(dataset: tf.data.Dataset):
    """
    Aggregate all the items in an array-like dataset (no batch dimension)
    into a single tensor in memory.
    
    If labels are present in the dataset, you will get back a tuple with two
    tensors. This is especially useful for error analysis when you need
    model.predict output to be in the same order as iterating over the input.
    """

    data_tensor = None
    labels_tensor = None
    for element in dataset:
        if isinstance(element, tuple):
            batch, labels = element
        else:
            batch = element
            labels = None

        if data_tensor is None:
            data_tensor = batch
        else:
            data_tensor = tf.concat([data_tensor, batch], axis=0)  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter

        if labels is not None:
            if labels_tensor is None:
                labels_tensor = labels
            else:
                labels_tensor = tf.concat([labels_tensor, labels], axis=0)  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    if labels_tensor is None:
        return data_tensor
    else:
        return (data_tensor, labels_tensor)
