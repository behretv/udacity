""" Class to handle files """


class FileHandler:
    def __init__(self):
        self.hyper_parameter = 'parameter/hyper.json'
        self.model_file = 'parameter/train_model.ckpt'
        self.training_file = 'data/train.p'
        self.validation_file = 'data/test.p'
        self.testing_file = 'data/valid.p'