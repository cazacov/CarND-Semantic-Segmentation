#!/usr/bin/env python3
import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
from sklearn.utils import shuffle


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights

    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)

    encoder_graph = tf.get_default_graph()

    image_tensor = encoder_graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob_tensor = encoder_graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out_tensor = encoder_graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out_tensor = encoder_graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out_tensor = encoder_graph.get_tensor_by_name(vgg_layer7_out_tensor_name)

    return image_tensor, keep_prob_tensor, layer3_out_tensor, layer4_out_tensor, layer7_out_tensor


tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function

    # Implement decoder by take VGG layer 7 output as input and upsampling it

    # Debug info
    print('vgg_layer3_out shape: ', vgg_layer3_out.shape)
    print('vgg_layer4_out shape: ', vgg_layer4_out.shape)
    print('vgg_layer7_out shape: ', vgg_layer7_out.shape)
    print('num_classes: ', num_classes)


    # Block 1

    # First apply 1x1 convolution
    dec1_conv = tf.layers.conv2d(vgg_layer7_out, num_classes,
        kernel_size=1,
        padding='same',
        kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=1e-3),  # Penalize large weight values
        name='dec1_conv')

    print('dec1_conv shape: ', dec1_conv.shape)

    # Deconvolution
    dec1_trans = tf.layers.conv2d_transpose(dec1_conv, num_classes,
                                        kernel_size=4,
                                        strides=(2, 2),
                                        padding='same',
                                        kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=1e-3),
                                        name='dec1_trans')

    print('dec1_trans shape: ', dec1_trans.shape)

    # Block 2

    # Prepare skip connection from encoder layer 4
    dec2_conv = tf.layers.conv2d(vgg_layer4_out, num_classes,
                                 kernel_size=1,
                                 padding='same',
                                 kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=1e-3),
                                 name='dec2_conv')

    print('dec2_conv shape: ', dec2_conv.shape)

    # Add direct and skip tensors
    dec2_add = tf.add(dec1_trans, dec2_conv, name='dec2_add')
    print('dec2_add shape: ', dec2_add.shape)

    dec2_trans = tf.layers.conv2d_transpose(dec2_add, num_classes,
                                            kernel_size=4,
                                            strides=(2, 2),
                                            padding='same',
                                            kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=1e-3),
                                            name='dec2_trans')
    print('dec2_trans shape: ', dec2_trans.shape)

    # Block 3

    # Prepare skip connection from encoder layer 3
    dec3_conv = tf.layers.conv2d(vgg_layer3_out, num_classes,
                                 kernel_size=1,
                                 padding='same',
                                 kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=1e-3),
                                 name='dec3_conv')
    print('dec3_conv shape: ', dec3_conv.shape)

    # Add direct and skip tensors
    dec3_add = tf.add(dec2_trans, dec3_conv, name='dec3_add')
    print('dec3_add shape: ', dec3_add.shape)


    dec3_trans = tf.layers.conv2d_transpose(dec3_add, num_classes,
                                            kernel_size=16,
                                            strides=(8, 8),
                                            padding='same',
                                            kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=1e-3),
                                            name='dec3_trans')
    print('dec3_trans shape: ', dec3_trans.shape)

    return dec3_trans
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function

    # Reshape tensor to convert 4-D in 2-D
    logits = tf.reshape(nn_last_layer, (-1, num_classes))

    # Cost function
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=correct_label, logits=logits)

    # Minimize loss
    cross_entropy_loss = tf.reduce_mean(cross_entropy)

    # Optimizer
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy_loss)

    return logits, optimizer, cross_entropy_loss

tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function

    for epoch in range(epochs):

        loss_sum = 0

        for images_train, labels_train in get_batches_fn(batch_size):

            images_train, labels_train = shuffle(images_train, labels_train)
            loss,_ = sess.run([cross_entropy_loss, train_op],
                     feed_dict={
                        input_image: images_train,
                        correct_label: labels_train,
                        keep_prob: 0.5,
                        learning_rate: 0.001
                     })
            loss_sum = loss_sum + loss

        print("Epoch: ", epoch, "  mean loss:", loss_sum / batch_size)


tests.test_train_nn(train_nn)



def run():
    num_classes = 2
    image_shape = (160, 576)  # KITTI dataset uses 160x576 images
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function

        # TODO: Train NN using the train_nn function

        # TODO: Save inference data using helper.save_inference_samples
        #  helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
