from unittest.mock import patch

import tensorflow as tf
import numpy as np
from sklearn.preprocessing import StandardScaler

import machine_learning.common.datasets as datasets

# TODO: consider mocking TF datasets?
class DatasetsTests(tf.test.TestCase):
    class FakeScaler(StandardScaler):
        def __init__(self):
            self.partial_fit_objects = []

        def transform(self, tensor):
            new_tensor = np.copy(tensor)
            new_tensor.fill(100.)
            return new_tensor
        def partial_fit(self, tensor):
            self.partial_fit_objects.append(tensor)
            
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

        # 3 batches with 2 samples each, 3 feature columns
        self.tensor = tf.constant([
            [[1, 2, 3],
             [4, 5, 6]],
            [[7, 8, 9],
             [10, 11, 12]],
            [[13, 14, 15],
             [16, 17, 18]],
        ])
        self.first_tensor_batch = self.tensor[0]
        # corresponds to shape of above tensor (1 label per sample)
        self.labels = tf.constant([
            [1, 0],
            [0, 1],
            [1, 1]
        ])
        self.first_labels_batch = self.labels[0]
        # 3 fields in 3 batches of two samples
        self.dictionary = {
            'field1': tf.constant([[1, -1], [4, -4], [7, -7]], tf.double),
            'field2': tf.constant([[2, -2], [5, -5], [8, -8]], tf.double),
            'field3': tf.constant([[3, -3], [6, -6], [9, -9]], tf.double),
        }
        self.first_dictionary_batch = {key: self.dictionary[key][0] for key in self.dictionary}
        # result of turning self.dictionary into a tensor where columns are in same order as keys
        self.tensorized_dictionary = [
            [[ 1.,  2.,  3.],
             [-1., -2., -3.]],

            [[ 4.,  5.,  6.],
             [-4., -5., -6.]],

            [[ 7.,  8.,  9.],
             [-7., -8., -9.]]
        ]

        self.tensor_dataset = tf.data.Dataset.from_tensor_slices(self.tensor)
        self.empty_dataset = tf.data.Dataset.from_tensor_slices(tf.zeros((0,)))
        self.labeled_dataset = tf.data.Dataset.from_tensor_slices((self.tensor, self.labels))

        def make_dictionary_dataset(dictionary_of_tensors):
            return {key: tf.data.Dataset.from_tensor_slices(dictionary_of_tensors[key]) for key in dictionary_of_tensors}

        self.dictionary_dataset = tf.data.Dataset.zip(make_dictionary_dataset(self.dictionary))
        self.labeled_dictionary_dataset = tf.data.Dataset.zip((self.dictionary_dataset, tf.data.Dataset.from_tensor_slices(self.labels)))

        self.printed_objects = []

    def make_fake_print(self):
        def fake_print(*args, **kwargs):
            self.printed_objects += args
            self.printed_objects += kwargs.values()
        return fake_print
    
    def test_count_batches(self):
        count = datasets.count_batches(self.tensor_dataset)

        self.assertEqual(count, 3)

    def test_count_batches_empty(self):
        count = datasets.count_batches(self.empty_dataset)

        self.assertEqual(count, 0)
    
    def test_count_batches_with_labels(self):
        count = datasets.count_batches(self.labeled_dataset)

        self.assertEqual(count, 3)
    
    def test_get_first_batch_with_tensor(self):
        batch = datasets.get_first_batch(self.tensor_dataset)

        self.assertIsInstance(batch, np.ndarray)
        self.assertAllEqual(self.first_tensor_batch, batch)
    
    def test_get_first_batch_with_labels(self):
        batch = datasets.get_first_batch(self.labeled_dataset)

        self.assertIsInstance(batch, tuple)
        self.assertIsInstance(batch[0], np.ndarray)
        self.assertAllEqual(self.first_tensor_batch, batch[0])
        self.assertAllEqual(self.first_labels_batch, batch[1])
    
    def test_get_first_batch_with_dictionary(self):
        batch = datasets.get_first_batch(self.dictionary_dataset)

        self.assertIsInstance(batch, dict)
        self.assertDictEqual(self.first_dictionary_batch, batch)
    
    def test_get_first_batch_with_empty(self):
        batch = datasets.get_first_batch(self.empty_dataset)
        self.assertIsNone(batch)
    
    def test_show_first_batch_with_tensor(self):
        with patch('builtins.print', new=self.make_fake_print()):
            datasets.show_first_batch(self.tensor_dataset)
        self.assertAllEqual([self.first_tensor_batch], self.printed_objects)

    def test_show_first_batch_with_dictionary(self):
        with patch('builtins.print', new=self.make_fake_print()):
            datasets.show_first_batch(self.dictionary_dataset)

        self.assertEqual(len(self.printed_objects), 1)
        self.assertIsInstance(self.printed_objects[0], dict)
        self.assertAllEqual(list(self.dictionary.keys()), list(self.printed_objects[0].keys()))
        self.assertAllEqual(list(self.first_dictionary_batch.values()), list(self.printed_objects[0].values()))
    
    def test_show_first_batch_with_labels(self):
        with patch('builtins.print', new=self.make_fake_print()):
            datasets.show_first_batch(self.labeled_dataset)
        
        self.assertEqual(len(self.printed_objects), 4)
        self.assertContainsSubsequence(self.printed_objects[0], 'Features')
        self.assertContainsSubsequence(self.printed_objects[2], 'Labels')
        self.assertAllEqual(self.first_tensor_batch, self.printed_objects[1])
        self.assertAllEqual(self.first_labels_batch, self.printed_objects[3])
    
    def test_show_first_batch_with_empty(self):
        with patch('builtins.print', new=self.make_fake_print()):
            datasets.show_first_batch(self.empty_dataset)

        self.assertAllEqual([None], self.printed_objects)

    def test_split_with_default_ratio(self):
        training,validation = datasets.split(self.tensor_dataset, num_batches=3)

        training_batches = list(training)
        validation_batches =list(validation)
        
        self.assertAllEqual(self.tensor[:2], training_batches)
        self.assertAllEqual(self.tensor[2:], validation_batches)

    def test_split_with_overridden_ratio(self):
        training,validation = datasets.split(self.tensor_dataset, num_batches=3, training_ratio = 0.5)

        training_batches = list(training)
        validation_batches =list(validation)
        
        self.assertAllEqual(self.tensor[:1], training_batches)
        self.assertAllEqual(self.tensor[1:], validation_batches)

    def test_split_with_empty(self):
        training,validation = datasets.split(self.empty_dataset, num_batches=0)

        training_batches = list(training)
        validation_batches =list(validation)
        
        self.assertEmpty(training_batches)
        self.assertEmpty(validation_batches)

    def test_split_with_no_validation_batches(self):
        training,validation = datasets.split(self.tensor_dataset, num_batches=4)

        training_batches = list(training)
        validation_batches =list(validation)
        
        self.assertAllEqual(self.tensor, training_batches)
        self.assertEmpty(validation_batches)
    
    def test_split_with_no_training_batches(self):
        training,validation = datasets.split(self.tensor_dataset, num_batches=0)

        training_batches = list(training)
        validation_batches =list(validation)
        
        self.assertEmpty(training_batches)
        self.assertAllEqual(self.tensor, validation_batches)
    
    def test_safe_batch_transformer_with_labels(self):
        transformed = self.labeled_dataset.map(datasets.safe_batch_transformer(lambda batch: 'gotcha!'))
        tensors,labels = tuple(zip(*list(transformed)))

        self.assertAllEqual(['gotcha!'] * 3, tensors)
        self.assertAllEqual(self.labels, labels)
    
    def test_safe_batch_transformer_without_labels(self):
        transformed = self.tensor_dataset.map(datasets.safe_batch_transformer(lambda batch: 'gotcha!'))

        self.assertAllEqual(['gotcha!'] * 3, list(transformed))

    def test_named_column_scaler(self):
        scalers = {
            'field2': DatasetsTests.FakeScaler(),
        }
        expected = {
            'field1': self.first_dictionary_batch['field1'],
            'field2': [100] * 2,
            'field3': self.first_dictionary_batch['field3'],
        }

        actual = next(iter(self.dictionary_dataset.map(datasets.named_column_scaler(scalers))))
        
        self.assertDictEqual(expected, actual)
    
    def test_named_column_scaler_with_labels(self):
        scalers = {
            'field2': DatasetsTests.FakeScaler(),
        }
        expected = {
            'field1': self.first_dictionary_batch['field1'],
            'field2': [100] * 2,
            'field3': self.first_dictionary_batch['field3'],
        }
        actual = next(iter(self.labeled_dictionary_dataset.map(datasets.named_column_scaler(scalers))))
        
        self.assertDictEqual(expected, actual[0])
        self.assertAllEqual([1, 0], actual[1])
        
    def test_remap_column_entries(self):
        mappings = {s: int(s)**2 for s in map(str, range(6))}
        values_tensor = tf.constant(['5', '4', '3', '2', '1'])

        transformed = datasets.remap_column_entries(values_tensor, mappings)

        self.assertAllEqual([25, 16, 9, 4,1], transformed)
    
    def test_named_column_oh_expander(self):
        one_hot_spec = {'field2': 8, 'field3': 9}
        expected = {
            'field1': tf.cast(self.dictionary['field1'], tf.int32)[0],
            'field2': [[0, 0, 1, 0, 0, 0, 0, 0], [0]*8],
            'field3': [[0, 0, 0, 1, 0, 0, 0, 0, 0], [0]*9],
        }
        dataset = self.dictionary_dataset.map(lambda d: {k: tf.cast(d[k], tf.int32) for k in d})

        expander = datasets.named_column_oh_expander(one_hot_spec)
        actual = next(iter(dataset.map(expander)))

        self.assertDictEqual(expected, actual)

    def test_named_column_oh_expander_with_labels(self):
        one_hot_spec = {'field2': 8, 'field3': 9}
        expected = {
            'field1': tf.cast(self.dictionary['field1'], tf.int32)[0],
            'field2': [[0, 0, 1, 0, 0, 0, 0, 0], [0]*8],
            'field3': [[0, 0, 0, 1, 0, 0, 0, 0, 0], [0]*9],
        }
        dataset = self.labeled_dictionary_dataset.map(lambda d,l: ({k: tf.cast(d[k], tf.int32) for k in d}, l))

        expander = datasets.named_column_oh_expander(one_hot_spec)
        actual = next(iter(dataset.map(expander)))

        self.assertDictEqual(expected, actual[0])
        self.assertAllEqual([1, 0], actual[1])
    
    def test_train_named_scalers(self):
        scalers = {
            'field2': DatasetsTests.FakeScaler(),
            'field3': DatasetsTests.FakeScaler(),
        }
        
        datasets.train_named_scalers(scalers, self.dictionary_dataset)

        self.assertEqual(len(scalers.keys()), 2)
        self.assertAllEqual(tf.reshape(self.dictionary['field2'], (3, 2, 1)), scalers['field2'].partial_fit_objects)
        self.assertAllEqual(tf.reshape(self.dictionary['field3'], (3, 2, 1)), scalers['field3'].partial_fit_objects)
    
    def test_train_named_scalers_with_labels(self):
        scalers = {
            'field2': DatasetsTests.FakeScaler(),
            'field3': DatasetsTests.FakeScaler(),
        }
        
        datasets.train_named_scalers(scalers, self.labeled_dictionary_dataset)

        self.assertEqual(len(scalers.keys()), 2)
        self.assertAllEqual(tf.reshape(self.dictionary['field2'], (3, 2, 1)), scalers['field2'].partial_fit_objects)
        self.assertAllEqual(tf.reshape(self.dictionary['field3'], (3, 2, 1)), scalers['field3'].partial_fit_objects)
    
    def test_to_matrix_default_type(self):
        transformed = self.dictionary_dataset.map(datasets.to_matrix())

        self.assertEqual(list(transformed)[0].dtype, tf.float32)    
        self.assertAllEqual(self.tensorized_dictionary, list(transformed))
    
    def test_to_matrix_specific_type(self):
        transformed = self.dictionary_dataset.map(datasets.to_matrix(dtype=tf.int32))

        self.assertEqual(list(transformed)[0].dtype, tf.int32)
        self.assertAllEqual(tf.cast(self.tensorized_dictionary, tf.int32), list(transformed))
    
    def test_to_matrix_with_labels(self):
        transformed = self.labeled_dictionary_dataset.map(datasets.to_matrix())
        tensor,labels = tuple(zip(*list(transformed)))

        self.assertEqual(list(transformed)[0][0].dtype, tf.float32)    
        self.assertAllEqual(self.tensorized_dictionary, tensor)
        self.assertAllEqual(self.labels, labels)

    def test_collect_tensors(self):
        tensor = datasets.collect_tensors(self.tensor_dataset)

        self.assertIsInstance(tensor, tf.Tensor)
        self.assertAllEqual([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]], tensor)
    
    def test_collect_tensors_with_labels(self):
        tensor,labels = datasets.collect_tensors(self.labeled_dataset)

        self.assertIsInstance(tensor, tf.Tensor)
        self.assertIsInstance(labels, tf.Tensor)
        self.assertAllEqual([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]], tensor)
        self.assertAllEqual([1, 0, 0, 1, 1, 1], labels)
    