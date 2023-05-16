from unittest.mock import patch

import tensorflow as tf

import machine_learning.common.error_analysis as error_analysis
import machine_learning.common.visualization as visualization

class ErrorAnalysisTests(tf.test.TestCase):
    def __init__(self, methodName='runTest'):
        super(ErrorAnalysisTests, self).__init__(methodName)

        self.tensor = tf.constant([
             [1, 2, 3],
             [4, 5, 6],
             [7, 8, 9],
             [10, 11, 12],
             [13, 14, 15],
             [16, 17, 18],
        ])
        self.labels = tf.constant([0, 0, 1, 0, 1, 1])

        self.printed_objects = []

    def make_fake_print(self):
        def fake_print(*args, **kwargs):
            if len(args) > 0:
                if args[0].startswith('['):
                    self.printed_objects.append(args[0][1:-1])
                elif args[0].startswith('Shape:'):
                    self.printed_objects.append(args[0][7:])
        return fake_print

    def make_fake_print_matrix(self):
        def fake_print_matrix(matrix):
            self.printed_objects.append(matrix)
        return fake_print_matrix
    
    def test_compute_error_analysis_matrices(self):
        predictions = tf.constant([0, 1, 1, 0, 0, 0]) # [tn, fp, tp, tn, fn, fn]
        expected = {
            'true_positives': [[7, 8, 9], ],
            'true_negatives': [[1, 2, 3], [10, 11, 12], ],
            'false_positives': [[4, 5, 6], ],
            'false_negatives': [[13, 14, 15], [16, 17, 18], ],
        }

        matrices = error_analysis.compute_error_analysis_matrices(self.tensor, self.labels, predictions)

        self.assertDictEqual(expected, matrices)
    
    def test_compute_error_analysis_matrices_with_empty_quadrant(self):
        predictions = tf.constant([0, 1, 0, 0, 0, 0]) # [tn, fp, fn, tn, fn, fn]
        expected = {
            'true_positives': tf.zeros((0,3)),
            'true_negatives': [[1, 2, 3], [10, 11, 12], ],
            'false_positives': [[4, 5, 6], ],
            'false_negatives': [[7, 8, 9], [13, 14, 15], [16, 17, 18], ],
        }

        matrices = error_analysis.compute_error_analysis_matrices(self.tensor, self.labels, predictions)

        self.assertDictEqual(expected, matrices)

    def test_print_error_analysis_matrices(self):
        matrices = {
            'true_positives': tf.zeros((0,3)),
            'true_negatives': tf.constant([[1, 2, 3], [10, 11, 12], ]),
            'false_positives': tf.constant([[4, 5, 6], ]),
            'false_negatives': tf.constant([[7, 8, 9], [13, 14, 15], [16, 17, 18], ]),
        }
        expected_prints = [
            'true_positives',
            '(0, 3)',
            matrices['true_positives'],
            'true_negatives',
            '(2, 3)',
            matrices['true_negatives'],
            'false_positives',
            '(1, 3)',
            matrices['false_positives'],
            'false_negatives',
            '(3, 3)',
            matrices['false_negatives'],
        ]

        with patch('builtins.print', new=self.make_fake_print()):
            with patch('machine_learning.common.visualization.print_matrix', new=self.make_fake_print_matrix()):
                error_analysis.print_error_analysis_matrices(matrices)

        # Have to do this manually because self.assertAllEqual fails and I'm not sure why
        self.assertEqual(len(expected_prints), len(self.printed_objects))
        for i in range(len(expected_prints)):
            if isinstance(expected_prints[i], str):
                self.assertEqual(expected_prints[i], self.printed_objects[i])
            else:
                self.assertAllEqual(expected_prints[i], self.printed_objects[i])
