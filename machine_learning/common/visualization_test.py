from unittest.mock import patch

import tensorflow as tf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt  # imported for mocking

import machine_learning.common.visualization as visualization


class VisualizationTests(tf.test.TestCase):

    class FakePlotAxis:

        def __init__(self):
            self.x_label = ''
            self.y_label = ''
            self.series = None

        def set_xlabel(self, label):
            self.x_label = label

        def set_ylabel(self, label):
            self.y_label = label

    class FakeHistory:

        def __init__(self, history):
            self.history = history

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

        self.dataframe = pd.DataFrame(
            [[1, 1, '3'], [1, 0, '6'], [3, 0, '9'], [4, 1, '12']],
            columns=['col1', 'col2', 'col3'])

        self.fake_plot_axis = VisualizationTests.FakePlotAxis()
        self.plotted_objects = []
        self.printed_objects = []

    def capture_series(self, series: pd.Series):
        self.fake_plot_axis.series = series

    def capture_plot(self, object):
        self.plotted_objects.append(object)

    def capture_print(self, *kargs, **kwargs):
        if len(kargs) == 0:
            self.printed_objects.append('newline')
        else:
            self.printed_objects.append(str(kargs[0]))
            if 'end' in kwargs:
                self.printed_objects.append('tab')

    def test_exmain_candidate_column(self):
        with patch.object(pd.Series, 'plot') as fake_plot:
            fake_plot.return_value = self.fake_plot_axis

            visualization.examine_candidate_column(
                self.dataframe, 'col1', 'Column 1', 'col2', 'Column 2',
                lambda s: self.capture_series(s))

        fake_plot.assert_called_once_with(kind='bar')
        self.assertEqual(self.fake_plot_axis.x_label, 'Column 1 (col1)')
        self.assertEqual(self.fake_plot_axis.y_label, '% Column 2')
        self.assertAllEqual([1, 3, 4], self.fake_plot_axis.series.index)
        self.assertAllEqual([50., 0., 100.], self.fake_plot_axis.series.values)
        self.assertEqual(self.fake_plot_axis.series.name, 'col2')
        self.assertEqual(self.fake_plot_axis.series.index.name, 'col1')

    def test_compute_truth_ratio_with_even_split(self):
        self.assertEqual(
            visualization.compute_truth_ratio(self.dataframe, 'col2'), 0.5)

    def test_compute_truth_ratio_with_skew(self):
        self.dataframe.at[1, 'col2'] = 1

        self.assertEqual(
            visualization.compute_truth_ratio(self.dataframe, 'col2'), 0.75)

    def test_compute_truth_ratio_with_zero(self):
        self.dataframe.at[0, 'col2'] = 0
        self.dataframe.at[3, 'col2'] = 0

        self.assertEqual(
            visualization.compute_truth_ratio(self.dataframe, 'col2'), 0.)

    def test_compute_truth_ratio_with_one(self):
        self.dataframe.at[1, 'col2'] = 1
        self.dataframe.at[2, 'col2'] = 1

        self.assertEqual(
            visualization.compute_truth_ratio(self.dataframe, 'col2'), 1.)

    def test_graph_training_stats(self):
        with patch('matplotlib.pyplot.plot') as fake_plot:
            fake_plot.side_effect = lambda x: self.capture_plot(x)
            with patch('matplotlib.pyplot.xlabel') as fake_xlabel:
                fake_xlabel.side_effect = lambda x: self.capture_plot(x)
                with patch('matplotlib.pyplot.title') as fake_title:
                    fake_title.side_effect = lambda x: self.capture_plot(x)
                    visualization.graph_training_stats(
                        VisualizationTests.FakeHistory({
                            'loss': 'Loss Value',
                            'accuracy': 'Accuracy Value',
                            'val_accuracy': 'Validation Accuracy Value',
                        }))
        self.assertAllEqual([
            'Loss Value',
            'Loss',
            'Epoch',
            'Accuracy Value',
            'Accuracy',
            'Epoch',
            'Validation Accuracy Value',
            'Validation Accuracy',
            'Epoch',
        ], self.plotted_objects)

    def test_print_matrix_with_tf(self):
        with patch('builtins.print') as fake_print:
            fake_print.side_effect = lambda *args, **kargs: self.capture_print(
                *args, **kargs)
            visualization.print_matrix(tf.constant([[1, 2], [3, 4]]))
        self.assertAllEqual([
            '1',
            'tab',
            '2',
            'tab',
            'newline',
            '3',
            'tab',
            '4',
            'tab',
            'newline',
        ], self.printed_objects)

    def test_print_matrix_with_np(self):
        with patch('builtins.print') as fake_print:
            fake_print.side_effect = lambda *args, **kargs: self.capture_print(
                *args, **kargs)
            visualization.print_matrix(np.array([[1, 2], [3, 4]]))
        self.assertAllEqual([
            '1',
            'tab',
            '2',
            'tab',
            'newline',
            '3',
            'tab',
            '4',
            'tab',
            'newline',
        ], self.printed_objects)

    def test_print_matrix_with_empty(self):
        with patch('builtins.print') as fake_print:
            fake_print.side_effect = lambda *args, **kargs: self.capture_print(
                *args, **kargs)
            visualization.print_matrix(tf.zeros(shape=()))
        self.assertAllEqual(['newline'], self.printed_objects)
