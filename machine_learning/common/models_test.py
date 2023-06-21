"""Tests for models.py."""

import tensorflow as tf

from machine_learning.common import models


class ModelsTests(tf.test.TestCase):
    """Tests for models.py."""

    def test_create_basic_ffn_logistic_regression(self):
        model = models.create_basic_ffn([1])

        self.assertEqual(len(model.layers), 1)
        self.assertEqual(model.layers[0].units, 1)
        self.assertEqual(model.layers[0].activation.__name__, 'sigmoid')

    def test_create_basic_ffn_linear_regression(self):
        model = models.create_basic_ffn([1], final_activation='linear')

        self.assertEqual(len(model.layers), 1)
        self.assertEqual(model.layers[0].units, 1)
        self.assertEqual(model.layers[0].activation.__name__, 'linear')

    def test_create_basic_ffn_multiple_outputs(self):
        model = models.create_basic_ffn([2], final_activation='linear')

        self.assertEqual(len(model.layers), 1)
        self.assertEqual(model.layers[0].units, 2)
        self.assertEqual(model.layers[0].activation.__name__, 'linear')

    def test_create_basic_ffn_hidden_layers(self):
        model = models.create_basic_ffn([10, 5, 1])

        layer_units = [layer.units for layer in model.layers]
        layer_activations = [
            layer.activation.__name__ for layer in model.layers
        ]

        self.assertAllEqual([10, 5, 1], layer_units)
        self.assertAllEqual(['relu', 'relu', 'sigmoid'], layer_activations)

    def test_create_basic_ffn_hidden_layers_with_activation_overrides(self):
        model = models.create_basic_ffn([10, 5, 1],
                                        hidden_activation='sigmoid',
                                        final_activation='relu')

        layer_units = [layer.units for layer in model.layers]
        layer_activations = [
            layer.activation.__name__ for layer in model.layers
        ]

        self.assertAllEqual([10, 5, 1], layer_units)
        self.assertAllEqual(['sigmoid', 'sigmoid', 'relu'], layer_activations)


if __name__ == '__main__':
    tf.test.main()
