import os
import sys
import tensorflow as tf
import pandas as pd
import pickle
from typing import Tuple

sys.path.append('..')
import common.datasets as datasets

INPUT_FOLDER = '/mnt/p/Datasets/titanic'  # This will be different on kaggle
TRAINING_DATA = os.path.join(INPUT_FOLDER, 'train.csv')
TEST_DATA = os.path.join(INPUT_FOLDER, 'test.csv')

MODEL_FOLDER = '/mnt/p/Models/kaggle-titanic'  # This will be different on kaggle
SCALER_FILE = os.path.join(MODEL_FOLDER, 'scalers.pkl')

OUTPUT_DATA = '/mnt/h/Temp/kaggle-titanic.csv'

DEFAULT_BATCH_SIZE = 10
BIGGER_BATCH_SIZE = 100
DATASET_SIZE = 891

ONE_HOT_SPECS = {'Sex': 2, 'Origin': 4}
SCALED_COLUMNS = ['Class', 'Siblings', 'AgeGroup', 'FareGroup',]

def load_data(filename: str = TRAINING_DATA, batch_size: int = DEFAULT_BATCH_SIZE, shuffle: bool = True, shuffle_seed: int = 4, label_name:str ='Survived') -> tf.data.Dataset:
    """Load a CSV dataset.

    Args:
        filename (str): The csv file.
        batch_size(int): The batch size to use for the dataset.
        shuffle)bool): Whether the data should be shuffled or not.
        shuffle_seed(int): The seed for shuffling.
        label_name(str): Label to use from the dataset columns (None to not use a label).

    Returns:
        The new (streaming with CPU prefetch) dataset, only 1 epoch.
    """

    dataset = tf.data.experimental.make_csv_dataset(
        filename,
        shuffle=shuffle,
        shuffle_seed=shuffle_seed,  # Want consistent randomization so I can compare models
        num_epochs=1,  # Leave the epoch counting to model.fit instead since no data augmentation needed
        label_name=label_name, # Ground truth (turns output from dict into tuple)
        batch_size=batch_size)
    return dataset

def transform_columns(batch, labels=None):
    """Transform a single batch of the dataset to have the columns we want.

    This is meant to be used as the argument to dataset.map().

    Args:
        batch: The batch to transform.
        labels: The label values for the batch, if present.  This will be None for inference.

    Returns:
        The transformed batch (and unaltered labels if present).
    """
    
    embark_to_class = {'S': 0, 'C': 1, 'Q': 2, '': 3}
    new_batch = {
        'Class': batch['Pclass'],
        'Sex': tf.cast(batch['Sex'] == b'male', tf.int32),
        'Siblings': batch['SibSp'],
        'Origin':  datasets.remap_column_entries(batch['Embarked'], embark_to_class),
        'AgeGroup': int(batch['Age'] // 10),  # found experimentally
        'FareGroup': int(batch['Fare'] // 50), # found experimentally
    }

    # TODO: consider using the new datasets.safe_batch_transformer here
    if labels == None:
        return new_batch
    else:
        return (new_batch, labels)

def extract_passenger_ids(batch):
    """Transform a single batch of the dataset to be (n,1) tensor of passenger IDs.

    This is meant to be used as an argument to dataset.map().
    
    Because this is meant to be used for test data, it will not work if you have labels in the dataset.
    """

    return tf.reshape(batch['PassengerId'], (-1, 1))

def save_scalers(scalers: dict) -> None:
    """Save dictionary of scalers so the trained data can be reused later."""

    with open(SCALER_FILE, 'wb') as f:
        pickle.dump(scalers,f)

def load_scalers() -> dict:
    """Load dictionary of scalers as saved by save_scalers."""

    with open(SCALER_FILE, 'rb') as f:
        return pickle.load(f)

def prepare_training_data_for_model(batch_size=BIGGER_BATCH_SIZE) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
    """Get training,validation dataset pair from CSV with all preprocessing applied."""
    raw_dataset = load_data(batch_size=batch_size)
    scalers = load_scalers()

    normalized_dataset = raw_dataset.map(transform_columns)\
                                    .map(datasets.named_column_oh_expander(ONE_HOT_SPECS))\
                                    .map(datasets.named_column_scaler(scalers))\
                                    .map(datasets.to_matrix())

    return datasets.split(normalized_dataset, num_batches=DATASET_SIZE / batch_size)

# TODO: consider common helpers with prepare_training_data_for_model (or don't - this way is pretty clear).
def prepare_test_data_for_model(batch_size=BIGGER_BATCH_SIZE) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
    """Get dataset pair (passengerIds,inputTensor) from CSV with all preprocessing applied.

    The shape of the PassengerId tensor will be (num_samples, 1) for easier concatenating.
    Because the dataset will not be shuffled, the two tensors can be iterated in parallel safely.
    """

    # I could have also used PassgnerId as the label as a hack, but I decided to keep it cleaner.
    raw_dataset = load_data(filename=TEST_DATA, batch_size=batch_size, shuffle=False, label_name=None)
    scalers = load_scalers()

    normalized_dataset = raw_dataset.map(transform_columns)\
                                    .map(datasets.named_column_oh_expander(ONE_HOT_SPECS))\
                                    .map(datasets.named_column_scaler(scalers))\
                                    .map(datasets.to_matrix())
    passenger_id_dataset = raw_dataset.map(extract_passenger_ids)

    return (passenger_id_dataset, normalized_dataset)

# TODO: consider ways to make this more general later (eg. break apart the csv part, etc.)
def test_model_and_create_csv(model: tf.keras.Model, index_dataset: tf.data.Dataset, input_dataset: tf.data.Dataset):
    """Run predictions using model in batches from input_dataset and create output csv with index_dataset entries as 1st column."""

    with open(OUTPUT_DATA, mode='w', newline='') as file:
        for batch_ids,batch in zip(index_dataset, input_dataset):
            batch_predictions = tf.cast(tf.reshape(model.predict_on_batch(batch) >= 0.5, (-1, 1)), tf.int32)
            batch_output = tf.concat([batch_ids, batch_predictions], axis=1)
            
            df = pd.DataFrame(batch_output.numpy(), columns=['PassengerId', 'Survived'])
            df.to_csv(file, header=file.tell() == 0, index=False)
