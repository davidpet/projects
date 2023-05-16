from typing import Sequence
import tensorflow as tf

# TODO: possibly add a way to pass activation functions instead of just activation strings if ever needed
# TODO: possibly add a way to specify input shape if ever needed
# TODO: incorporate input layer to avoid retracing in model.fit()
def create_basic_ffn(layer_units: Sequence[int], final_activation: str = 'sigmoid', hidden_activation: str = 'relu') -> tf.keras.Model:
    """Create a basic keras sequential model with dense layers having the given units per layer."""

    hidden_layers = len(layer_units) - 1
    layer_activations = [hidden_activation] * hidden_layers + [final_activation]

    return tf.keras.models.Sequential([tf.keras.layers.Dense(layer_units[i], layer_activations[i]) 
                                        for i in range(len(layer_units))])
 