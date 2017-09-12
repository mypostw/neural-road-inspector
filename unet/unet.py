import numpy as np
from keras.models import *
from keras.layers import Input, merge, Conv2D, Convolution2D, MaxPooling2D, UpSampling2D, Cropping2D, ZeroPadding2D, Dropout, Cropping2D, BatchNormalization, Activation
from keras.optimizers import *
from keras.callbacks import ModelCheckpoint, LearningRateScheduler
from keras import backend as keras

K.set_image_dim_ordering('tf')  # Tensorflow dimension ordering

class Unet(object):
	def __init__(self, num_channels=3, img_rows = 256, img_cols = 256):
		"""
		Both row and col dimensions should be multiple of 2^4.  Otherwise, we will see erros from merge layer.
			ValueError: "concat" mode can only merge layers with matching output shapes except for the concat axis.
			Layer shapes: [(None, 512, 160, 238), (None, 256, 160, 239)]
		"""
		self.num_channels = num_channels
		self.img_rows = img_rows
		self.img_cols = img_cols

	def get_model(self, model_id):
		model_dict = {
			'Unet': self.get_unet,
			'Unet_Mini': self.get_unet_mini,
			'Unet_Tiny': self.get_unet_tiny,
			'Unet_Tiny': self.get_unet_tiny,
			'Unet_Tiny_D4': self.get_unet_tiny_depth4,
			'Unet_Tiny_D4_BN': self.get_unet_tiny_depth4_bn,
			'Unet_Level7': self.get_unet_level_7,
			'Unet_Level8': self.get_unet_level_8,
		}
		return model_dict[model_id]()

	def get_crop_shape(self, target, refer):
		"""Assumption: Theano ordering where height is at index 2 and width is at index 3.
		   Tensorflow sould have height at index 1 and width at index 2"""
		width_index = 3 # Theano ordering
		height_index = 2 # Theano ordering

		# width
		cw = (keras.int_shape(target)[width_index] - keras.int_shape(refer)[width_index])
		assert (cw >= 0)
		if cw % 2 != 0:
			cw1, cw2 = int(cw/2), int(cw/2) + 1
		else:
			cw1, cw2 = int(cw/2), int(cw/2)
		# height
		ch = (keras.int_shape(target)[height_index] - keras.int_shape(refer)[height_index])
		assert (ch >= 0)
		if ch % 2 != 0:
			ch1, ch2 = int(ch/2), int(ch/2) + 1
		else:
			ch1, ch2 = int(ch/2), int(ch/2)

		return (ch1, ch2), (cw1, cw2)

	# original work on u-net: https://lmb.informatik.uni-freiburg.de/people/ronneber/u-net/
	# note: original u-net use border_mode='valid' instead of 'same'
	# code borrowed from: https://github.com/jocicmarko/ultrasound-nerve-segmentation/blob/51dc5a1b2b77ac5b75dda77f3577c7c6bcf2b2a9/train.py
	# they use a differnent lose function
	def get_unet(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv1 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(inputs)
		conv1 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(pool1)
		conv2 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(pool2)
		conv3 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(pool3)
		conv4 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(conv4)
		pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

		conv5 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(pool4)
		conv5 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(conv5)

		up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv4], mode='concat', concat_axis=1)
		conv6 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(up6)
		conv6 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv3], mode='concat', concat_axis=1)
		conv7 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(up7)
		conv7 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv7)

		up8 = merge([UpSampling2D(size=(2, 2))(conv7), conv2], mode='concat', concat_axis=1)
		conv8 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(up8)
		conv8 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv8)

		up9 = merge([UpSampling2D(size=(2, 2))(conv8), conv1], mode='concat', concat_axis=1)
		conv9 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(up9)
		conv9 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv9)

		conv10 = Convolution2D(1, 1, 1, activation='sigmoid')(conv9)

		model = Model(input=inputs, output=conv10)

		return model

	def get_unet_level_7(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv0 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(inputs)
		conv0 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv0)
		pool0 = MaxPooling2D(pool_size=(2, 2))(conv0)

		conv1 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(pool0)
		conv1 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(pool1)
		conv2 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(pool2)
		conv3 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(pool3)
		conv4 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv4)
		pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

		conv5 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(pool4)
		conv5 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(conv5)
		pool5 = MaxPooling2D(pool_size=(2, 2))(conv5)

		conv6 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(pool5)
		conv6 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv5], mode='concat', concat_axis=1)
		conv7 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(up7)
		conv7 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(conv7)

		up8 = merge([UpSampling2D(size=(2, 2))(conv7), conv4], mode='concat', concat_axis=1)
		conv8 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(up8)
		conv8 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv8)

		up9 = merge([UpSampling2D(size=(2, 2))(conv8), conv3], mode='concat', concat_axis=1)
		conv9 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(up9)
		conv9 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv9)

		up10 = merge([UpSampling2D(size=(2, 2))(conv9), conv2], mode='concat', concat_axis=1)
		conv10 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(up10)
		conv10 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv10)

		up11 = merge([UpSampling2D(size=(2, 2))(conv10), conv1], mode='concat', concat_axis=1)
		conv11 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(up11)
		conv11 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv11)

		up12 = merge([UpSampling2D(size=(2, 2))(conv11), conv0], mode='concat', concat_axis=1)
		conv12 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(up12)
		conv12 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv12)

		conv13 = Convolution2D(1, 1, 1, activation='sigmoid')(conv12)

		model = Model(input=inputs, output=conv13)

		return model

	def get_unet_level_8(self):
		"""
			Apply Cropping2D similar to : https://github.com/zizhaozhang/unet-tensorflow-keras/blob/master/model.py 
			Cropping before merge to allow arbitrary image dimensions 
		"""
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv0 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(inputs)
		conv0 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv0)
		pool0 = MaxPooling2D(pool_size=(2, 2))(conv0)

		conv1 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(pool0)
		conv1 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(pool1)
		conv2 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(pool2)
		conv3 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(pool3)
		conv4 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv4)
		pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

		conv5 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(pool4)
		conv5 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(conv5)
		pool5 = MaxPooling2D(pool_size=(2, 2))(conv5)

		conv6 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(pool5)
		conv6 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(conv6)
		pool6 = MaxPooling2D(pool_size=(2, 2))(conv6)

		# bottom of the UNet
		conv7 = Convolution2D(1024, 3, 3, activation='relu', border_mode='same')(pool6)
		conv7 = Convolution2D(1024, 3, 3, activation='relu', border_mode='same')(conv7)

		up_conv7 = UpSampling2D(size=(2, 2))(conv7)
		ch, cw = self.get_crop_shape(conv6, up_conv7)
		crop_conv6 = Cropping2D(cropping=(ch,cw))(conv6)
		up8 = merge([up_conv7, crop_conv6], mode='concat', concat_axis=1)
		conv8 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(up8)
		conv8 = Convolution2D(512, 3, 3, activation='relu', border_mode='same')(conv8)

		up_conv8 = UpSampling2D(size=(2, 2))(conv8)
		ch, cw = self.get_crop_shape(conv5, up_conv8)
		crop_conv5 = Cropping2D(cropping=(ch,cw))(conv5)
		up9 = merge([up_conv8, crop_conv5], mode='concat', concat_axis=1)
		conv9 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(up9)
		conv9 = Convolution2D(256, 3, 3, activation='relu', border_mode='same')(conv9)

		up_conv9 = UpSampling2D(size=(2, 2))(conv9)
		ch, cw = self.get_crop_shape(conv4, up_conv9)
		crop_conv4 = Cropping2D(cropping=(ch,cw))(conv4)		
		up10 = merge([up_conv9, crop_conv4], mode='concat', concat_axis=1)
		conv10 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(up10)
		conv10 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv10)

		up_conv10 = UpSampling2D(size=(2, 2))(conv10)
		ch, cw = self.get_crop_shape(conv3, up_conv10)
		crop_conv3 = Cropping2D(cropping=(ch,cw))(conv3)
		up11 = merge([up_conv10, crop_conv3], mode='concat', concat_axis=1)
		conv11 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(up11)
		conv11 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv11)

		up_conv11 = UpSampling2D(size=(2, 2))(conv11)
		ch, cw = self.get_crop_shape(conv2, up_conv11)
		crop_conv2 = Cropping2D(cropping=(ch,cw))(conv2)
		up12 = merge([up_conv11, crop_conv2], mode='concat', concat_axis=1)
		conv12 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(up12)
		conv12 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv12)

		up_conv12 = UpSampling2D(size=(2, 2))(conv12)
		ch, cw = self.get_crop_shape(conv1, up_conv12)
		crop_conv1 = Cropping2D(cropping=(ch,cw))(conv1)
		up13 = merge([up_conv12, crop_conv1], mode='concat', concat_axis=1)
		conv13 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(up13)
		conv13 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv13)

		up_conv13 = UpSampling2D(size=(2, 2))(conv13)
		ch, cw = self.get_crop_shape(conv0, up_conv13)
		crop_conv0 = Cropping2D(cropping=(ch,cw))(conv0)
		up14 = merge([up_conv13, crop_conv0], mode='concat', concat_axis=1)
		conv14 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(up14)
		conv14 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv14)

		# Must add padding to match Input dimenions. Otherwise:
		# ValueError: GpuElemwise. Input dimension mis-match. Input 1 (indices start at 0) has shape[0] == 2293760, but the output's size on that axis is 2455040.
		ch, cw = self.get_crop_shape(inputs, conv14)
		padding14 = ZeroPadding2D(padding=(ch[0], ch[1], cw[0], cw[1]))(conv14)  # (top_pad, bottom_pad, left_pad, right_pad)
		conv15 = Convolution2D(1, 1, 1, activation='sigmoid')(padding14)

		model = Model(input=inputs, output=conv15)

		return model

	def get_unet_mini(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv1 = Conv2D(16, (3, 3), padding="same", activation="relu")(inputs)
		conv1 = Conv2D(16, (3, 3), padding="same", activation="relu")(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Conv2D(32, (3, 3), padding="same", activation="relu")(pool1)
		conv2 = Conv2D(32, (3, 3), padding="same", activation="relu")(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Conv2D(64, (3, 3), padding="same", activation="relu")(pool2)
		conv3 = Conv2D(64, (3, 3), padding="same", activation="relu")(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Conv2D(128, (3, 3), padding="same", activation="relu")(pool3)
		conv4 = Conv2D(128, (3, 3), padding="same", activation="relu")(conv4)
		pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

		conv5 = Conv2D(256, (3, 3), padding="same", activation="relu")(pool4)
		conv5 = Conv2D(256, (3, 3), padding="same", activation="relu")(conv5)

		up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv4], mode='concat', concat_axis=3) # concat_axis depends on Tensorflow vs theano
		conv6 = Conv2D(128, (3, 3), padding="same", activation="relu")(up6)
		conv6 = Conv2D(128, (3, 3), padding="same", activation="relu")(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv3], mode='concat', concat_axis=3)
		conv7 = Conv2D(64, (3, 3), padding="same", activation="relu")(up7)
		conv7 = Conv2D(64, (3, 3), padding="same", activation="relu")(conv7)

		up8 = merge([UpSampling2D(size=(2, 2))(conv7), conv2], mode='concat', concat_axis=3)
		conv8 = Conv2D(32, (3, 3), padding="same", activation="relu")(up8)
		conv8 = Conv2D(32, (3, 3), padding="same", activation="relu")(conv8)

		up9 = merge([UpSampling2D(size=(2, 2))(conv8), conv1], mode='concat', concat_axis=3)
		conv9 = Conv2D(16, (3, 3), padding="same", activation="relu")(up9)
		conv9 = Conv2D(16, (3, 3), padding="same", activation="relu")(conv9)

		conv10 = Conv2D(1, (1, 1), activation='sigmoid')(conv9)

		model = Model(inputs=[inputs], outputs=[conv10])
		return model

	def get_unet_mini_bn(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv1 = Convolution2D(16, 3, 3, border_mode='same')(inputs)
		conv1 = BatchNormalization()(conv1)
		conv1 = Activation('relu')(conv1)
		conv1 = Convolution2D(16, 3, 3, border_mode='same')(conv1)
		conv1 = BatchNormalization()(conv1)
		conv1 = Activation('relu')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(32, 3, 3, border_mode='same')(pool1)
		conv2 = BatchNormalization()(conv2)
		conv2 = Activation('relu')(conv2)
		conv2 = Convolution2D(32, 3, 3, border_mode='same')(conv2)
		conv2 = BatchNormalization()(conv2)
		conv2 = Activation('relu')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(64, 3, 3, border_mode='same')(pool2)
		conv3 = BatchNormalization()(conv3)
		conv3 = Activation('relu')(conv3)
		conv3 = Convolution2D(64, 3, 3, border_mode='same')(conv3)
		conv3 = BatchNormalization()(conv3)
		conv3 = Activation('relu')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(128, 3, 3, border_mode='same')(pool3)
		conv4 = BatchNormalization()(conv4)
		conv4 = Activation('relu')(conv4)
		conv4 = Convolution2D(128, 3, 3, border_mode='same')(conv4)
		conv4 = BatchNormalization()(conv4)
		conv4 = Activation('relu')(conv4)
		pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

		conv5 = Convolution2D(256, 3, 3, border_mode='same')(pool4)
		conv5 = BatchNormalization()(conv5)
		conv5 = Activation('relu')(conv5)
		conv5 = Convolution2D(256, 3, 3, border_mode='same')(conv5)
		conv5 = BatchNormalization()(conv5)
		conv5 = Activation('relu')(conv5)

		up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv4], mode='concat', concat_axis=1)
		conv6 = Convolution2D(128, 3, 3, border_mode='same')(up6)
		conv6 = BatchNormalization()(conv6)
		conv6 = Activation('relu')(conv6)
		conv6 = Convolution2D(128, 3, 3, border_mode='same')(conv6)
		conv6 = BatchNormalization()(conv6)
		conv6 = Activation('relu')(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv3], mode='concat', concat_axis=1)
		conv7 = Convolution2D(64, 3, 3, border_mode='same')(up7)
		conv7 = BatchNormalization()(conv7)
		conv7 = Activation('relu')(conv7)
		conv7 = Convolution2D(64, 3, 3, border_mode='same')(conv7)
		conv7 = BatchNormalization()(conv7)
		conv7 = Activation('relu')(conv7)

		up8 = merge([UpSampling2D(size=(2, 2))(conv7), conv2], mode='concat', concat_axis=1)
		conv8 = Convolution2D(32, 3, 3, border_mode='same')(up8)
		conv8 = BatchNormalization()(conv8)
		conv8 = Activation('relu')(conv8)
		conv8 = Convolution2D(32, 3, 3, border_mode='same')(conv8)
		conv8 = BatchNormalization()(conv8)
		conv8 = Activation('relu')(conv8)

		up9 = merge([UpSampling2D(size=(2, 2))(conv8), conv1], mode='concat', concat_axis=1)
		conv9 = Convolution2D(16, 3, 3, border_mode='same')(up9)
		conv9 = BatchNormalization()(conv9)
		conv9 = Activation('relu')(conv9)
		conv9 = Convolution2D(16, 3, 3, border_mode='same')(conv9)
		conv9 = BatchNormalization()(conv9)
		conv9 = Activation('relu')(conv9)

		conv10 = Convolution2D(1, 1, 1, activation='sigmoid')(conv9)

		model = Model(input=inputs, output=conv10)

		return model

	def get_unet_tiny(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv1 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(inputs)
		conv1 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(pool1)
		conv2 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(pool2)
		conv3 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(pool3)
		conv4 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv4)
		pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

		conv5 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(pool4)
		conv5 = Convolution2D(128, 3, 3, activation='relu', border_mode='same')(conv5)

		up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv4], mode='concat', concat_axis=1)
		conv6 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(up6)
		conv6 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv3], mode='concat', concat_axis=1)
		conv7 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(up7)
		conv7 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv7)

		up8 = merge([UpSampling2D(size=(2, 2))(conv7), conv2], mode='concat', concat_axis=1)
		conv8 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(up8)
		conv8 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv8)

		up9 = merge([UpSampling2D(size=(2, 2))(conv8), conv1], mode='concat', concat_axis=1)
		conv9 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(up9)
		conv9 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv9)

		conv10 = Convolution2D(1, 1, 1, activation='sigmoid')(conv9)

		model = Model(input=inputs, output=conv10)

		return model

	def get_unet_tiny_depth4(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv1 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(inputs)
		conv1 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(pool1)
		conv2 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(pool2)
		conv3 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(pool3)
		conv4 = Convolution2D(64, 3, 3, activation='relu', border_mode='same')(conv4)

		up5 = merge([UpSampling2D(size=(2, 2))(conv4), conv3], mode='concat', concat_axis=1)
		conv5 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(up5)
		conv5 = Convolution2D(32, 3, 3, activation='relu', border_mode='same')(conv5)

		up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv2], mode='concat', concat_axis=1)
		conv6 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(up6)
		conv6 = Convolution2D(16, 3, 3, activation='relu', border_mode='same')(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv1], mode='concat', concat_axis=1)
		conv7 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(up7)
		conv7 = Convolution2D(8, 3, 3, activation='relu', border_mode='same')(conv7)

		conv8 = Convolution2D(1, 1, 1, activation='sigmoid')(conv7)

		model = Model(input=inputs, output=conv8)

		return model


	def get_unet_tiny_depth4_bn(self):
		inputs = Input((self.img_rows, self.img_cols, self.num_channels))

		conv1 = Convolution2D(8, 3, 3, border_mode='same')(inputs)
		conv1 = BatchNormalization()(conv1)
		conv1 = Activation('relu')(conv1)
		conv1 = Convolution2D(8, 3, 3, border_mode='same')(conv1)
		conv1 = BatchNormalization()(conv1)
		conv1 = Activation('relu')(conv1)
		pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

		conv2 = Convolution2D(16, 3, 3, border_mode='same')(pool1)
		conv2 = BatchNormalization()(conv2)
		conv2 = Activation('relu')(conv2)
		conv2 = Convolution2D(16, 3, 3, border_mode='same')(conv2)
		conv2 = BatchNormalization()(conv2)
		conv2 = Activation('relu')(conv2)
		pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

		conv3 = Convolution2D(32, 3, 3, border_mode='same')(pool2)
		conv3 = BatchNormalization()(conv3)
		conv3 = Activation('relu')(conv3)
		conv3 = Convolution2D(32, 3, 3, border_mode='same')(conv3)
		conv3 = BatchNormalization()(conv3)
		conv3 = Activation('relu')(conv3)
		pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

		conv4 = Convolution2D(64, 3, 3, border_mode='same')(pool3)
		conv4 = BatchNormalization()(conv4)
		conv4 = Activation('relu')(conv4)
		conv4 = Convolution2D(64, 3, 3, border_mode='same')(conv4)
		conv4 = BatchNormalization()(conv4)
		conv4 = Activation('relu')(conv4)

		up5 = merge([UpSampling2D(size=(2, 2))(conv4), conv3], mode='concat', concat_axis=1)
		conv5 = Convolution2D(32, 3, 3, border_mode='same')(up5)
		conv5 = BatchNormalization()(conv5)
		conv5 = Activation('relu')(conv5)
		conv5 = Convolution2D(32, 3, 3, border_mode='same')(conv5)
		conv5 = BatchNormalization()(conv5)
		conv5 = Activation('relu')(conv5)

		up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv2], mode='concat', concat_axis=1)
		conv6 = Convolution2D(16, 3, 3, border_mode='same')(up6)
		conv6 = BatchNormalization()(conv6)
		conv6 = Activation('relu')(conv6)
		conv6 = Convolution2D(16, 3, 3, border_mode='same')(conv6)
		conv6 = BatchNormalization()(conv6)
		conv6 = Activation('relu')(conv6)

		up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv1], mode='concat', concat_axis=1)
		conv7 = Convolution2D(8, 3, 3, border_mode='same')(up7)
		conv7 = BatchNormalization()(conv7)
		conv7 = Activation('relu')(conv7)
		conv7 = Convolution2D(8, 3, 3, border_mode='same')(conv7)
		conv7 = BatchNormalization()(conv7)
		conv7 = Activation('relu')(conv7)

		conv8 = Convolution2D(1, 1, 1, activation='sigmoid')(conv7)

		model = Model(input=inputs, output=conv8)

		return model