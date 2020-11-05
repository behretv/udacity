""" This files handles the sessions, to train and test a neural network """
import logging
import math

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.utils import shuffle
from tqdm import tqdm
from traffic_sign_detection.data_handler import DataType, DataHandler
from traffic_sign_detection.file_handler import FileHandler


class SessionHandler:

    def __init__(self, files: FileHandler, data: DataHandler):
        self.__logger = logging.getLogger(SessionHandler.__name__)
        self.__data = data
        self.__file = files.model_file
        self.__cnn = None  # cnn
        self.__params = None  # hyper.parameter
        self.__session = None
        self.__saver = None
        self.list_total_valid_accuracy = []
        self.list_train_accuracy = []
        self.list_valid_accuracy = []
        self.list_loss = []
        self.list_batch = []
        self.log_batch_step = 50

    @property
    def cnn(self):
        assert self.__cnn is not None
        return self.__cnn

    @cnn.setter
    def cnn(self, value):
        assert value is not None
        self.__cnn = value

    @property
    def params(self):
        assert self.__params is not None
        return self.__params

    @params.setter
    def params(self, value):
        assert value is not None
        self.__params = value

    @property
    def session(self):
        assert self.__session is not None
        return self.__session

    @session.setter
    def session(self, value):
        assert value is not None
        self.__logger.info("+++Session started!+++")
        self.__session = value

    def close(self):
        self.session.close()
        self.__logger.info("+++Session closed!+++")

    def __init_session(self):
        self.__saver = tf.train.Saver()
        self.session = tf.Session()
        self.session.run(tf.global_variables_initializer())

    def __extract_batch(self):

    def train(self, step):
        self.__logger.info("{}# Training...".format(id))

        self.list_total_valid_accuracy = []
        self.list_train_accuracy = []
        self.list_valid_accuracy = []
        self.list_loss = []
        self.list_batch = []

        feature_train, label_train = self.__data.get_shuffled_data(DataType.TRAIN)
        feature_valid, label_valid = self.__data.get_shuffled_data(DataType.VALID)
        batch_count = int(math.ceil(len(feature_train) / self.params.batch_size))

        self.__init_session()

        for i in range(self.params.epochs):
            # Progress bar

            batches_pbar = tqdm(range(batch_count), desc=self.__progress_msg(i), unit='batches')

            feature_train, label_train = shuffle(feature_train, label_train)

            for batch_i in batches_pbar:
                batch_start = batch_i * self.params.batch_size
                batch_end = batch_start + self.params.batch_size

                train_batch = self.__generate_feed_dict(feature_train, label_train, batch_start, batch_end, 0.5)
                loss_batch = self.__generate_feed_dict(feature_train, label_train, batch_start, batch_end, 1.0)
                valid_feed = self.__generate_feed_dict(feature_valid, label_valid, batch_start, batch_end, 1.0)

                self.__session.run(self.cnn.optimizer, feed_dict=train_batch)
                loss = self.__session.run(self.cnn.cost, feed_dict=loss_batch)

                # Log every 50 batches
                if not batch_i % self.log_batch_step:
                    # Calculate Training and Validation accuracy
                    train_accuracy = self.session.run(self.cnn.accuracy, feed_dict=loss_batch)
                    valid_accuracy = self.session.run(self.cnn.accuracy, feed_dict=valid_feed)

                    previous_batch = self.list_batch[-1] if self.list_batch else 0
                    self.list_batch.append(self.log_batch_step + previous_batch)
                    self.list_train_accuracy.append(train_accuracy)
                    self.list_valid_accuracy.append(valid_accuracy)
                    self.list_loss.append(loss)

            self.list_total_valid_accuracy.append(self.validate(feature_valid, label_valid))
            if not self.__is_accuracy_improved(self.list_total_valid_accuracy):
                break

        self.__save_session(step)

        return self.list_total_valid_accuracy[-1]

    def validate(self, feature_valid, label_valid):
        n_features = len(feature_valid)

        total_accuracy = 0
        for i_start in range(0, n_features, self.params.batch_size):
            i_end = i_start + self.params.batch_size
            tmp_features = feature_valid[i_start:i_end]
            tmp_labels = label_valid[i_start:i_end]

            valid_batch = self.__generate_feed_dict(tmp_features, tmp_labels)
            tmp_accuracy = self.session.run(self.cnn.accuracy, feed_dict=valid_batch)

            total_accuracy += (tmp_accuracy * len(tmp_features))
        return total_accuracy / n_features

    def test(self, step, datatype: DataType):
        filename = self.__file + str(step)
        self.__logger.info("Restore model: {}".format(filename))

        # Runs saved session
        saver = tf.train.Saver()
        feature_test, label_test = self.__data.get_shuffled_data(datatype)
        with tf.Session() as sess:
            saver.restore(sess, filename)
            feed_dict = self.__generate_feed_dict(feature_test, label_test)
            test_accuracy = sess.run(self.cnn.accuracy, feed_dict=feed_dict)

        return test_accuracy

    def visualize_training_process(self):
        batches = self.list_batch
        loss_batch = self.list_loss
        train_acc_batch = self.list_train_accuracy
        valid_acc_batch = self.list_valid_accuracy

        loss_plot = plt.subplot(211)
        loss_plot.set_title('Loss')
        loss_plot.plot(batches, loss_batch, 'g')
        loss_plot.set_xlim([batches[0], batches[-1]])
        acc_plot = plt.subplot(212)
        acc_plot.set_title('Accuracy')
        acc_plot.plot(batches, train_acc_batch, 'r', label='Training Accuracy')
        acc_plot.plot(batches, valid_acc_batch, 'x', label='Validation Accuracy')
        acc_plot.set_ylim([0, 1.0])
        acc_plot.set_xlim([batches[0], batches[-1]])
        acc_plot.legend(loc=4)
        plt.tight_layout()
        plt.show()

    def __generate_feed_dict(self, feature, label, start=0, end=-1, keep_prob=1.0):
        return {
            self.cnn.tf_features: feature[start:end],
            self.cnn.tf_labels: label[start:end],
            self.cnn.tf_keep_prob: keep_prob
        }

    def __progress_msg(self, i):
        list_accuracy = self.list_total_valid_accuracy
        if i > 0:
            msg = 'Previous Accuracy={:.3f} Epoch {:>2}/{}'.format(list_accuracy[i - 1], i + 1, self.params.epochs)
        else:
            msg = 'Epoch {:>2}/{}'.format(i + 1, self.params.epochs)
        return msg

    def __is_accuracy_improved(self, list_accuracy):
        list_accuracy = np.array(list_accuracy)
        is_improved = True
        if len(list_accuracy) > 3:
            mean_diff = np.mean(np.diff(list_accuracy[-4:]))
            if mean_diff < 0.001:
                self.__logger.info("Abort, accuracy did not increase enough!")
                is_improved = False
        return is_improved

    def __save_session(self, step):
        filename = self.__file + str(step)
        self.__logger.info("Save model as: {}".format(filename))
        self.__saver.save(self.session, filename)

