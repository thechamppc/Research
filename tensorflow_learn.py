#!/usr/bin/python3

"""
This script reads app_permission_vectors.json (written by parse_xml.py) and
feeds the data into a tensorflow "neural network" to try to learn from it.
"""

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior() 
import numpy as np
import json
import math
import random
import sys
from configparser import ConfigParser

__author__='mwleeds'

def main():
    config = ConfigParser()
    config.read('/config.ini')
    LEARNING_RATE = config.getfloat('AMA', 'LEARNING_RATE')
    NUM_CHUNKS = config.getint('AMA', 'NUM_CHUNKS')
    SHUFFLE_CHUNKS = config.getboolean('AMA', 'SHUFFLE_CHUNKS')
    DECAY_RATE = config.getfloat('AMA', 'DECAY_RATE')

    # load the data from a file
    with open(sys.argv[1]) as infile:
        dataset = json.load(infile)

    # placeholder for any number of bit vectors
    x = tf.placeholder(tf.float32, [None, len(dataset['features'])])

    # weights for each synapse
    W = tf.Variable(tf.zeros([len(dataset['features']), 2]))

    b = tf.Variable(tf.zeros([2]))

    # results
    y = tf.nn.softmax(tf.matmul(x, W) + b)

    # placeholder for correct answers
    y_ = tf.placeholder(tf.float32, [None, 2])

    cross_entropy = -tf.reduce_sum(y_*tf.log(y))
    init = tf.initialize_all_variables()

    sess = tf.Session()

    sess.run(init)

    #TODO make a clean interface for this
    #TODO make sure the training sample contains reasonable proportions of benign/malicious
    malicious_app_names = [app for app in dataset['apps'] if dataset['apps'][app]['malicious'] == [1,0]]
    benign_app_names = [app for app in dataset['apps'] if dataset['apps'][app]['malicious'] == [0,1]]
    # break up the data into chunks for training and testing
    malicious_app_name_chunks = list(chunks(malicious_app_names, math.floor(len(dataset['apps']) / NUM_CHUNKS)))
    benign_app_name_chunks = list(chunks(benign_app_names, math.floor(len(dataset['apps']) / NUM_CHUNKS)))
    if SHUFFLE_CHUNKS:
        random.shuffle(malicious_app_name_chunks)
        random.shuffle(benign_app_name_chunks)

    # the first chunk of each will be used for testing (and the rest for training)
    for i in range(int(sys.argv[2])):
        # decayed Learning Rate increases accuracy by 3-5%
        decayed_learning_rate = tf.train.exponential_decay(LEARNING_RATE, i, 1, DECAY_RATE, staircase=False)
        train_step = tf.train.GradientDescentOptimizer(decayed_learning_rate).minimize(cross_entropy)

        j = random.randrange(1, len(malicious_app_name_chunks))
        k = random.randrange(1, len(benign_app_name_chunks))
        app_names_chunk = malicious_app_name_chunks[j] + benign_app_name_chunks[k]
        batch_xs = [dataset['apps'][app]['vector'] for app in app_names_chunk]
        batch_ys = [dataset['apps'][app]['malicious'] for app in app_names_chunk]
        sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys})

    feature_weights=sess.run([W])[0]
    # store feature weights that were calculated. Used by match_features.py
    with open ('feature_weights.json','w') as f:
        json.dump(feature_weights.tolist(),f)

    app_names_chunk = malicious_app_name_chunks[0] + benign_app_name_chunks[0]
    test_xs = [dataset['apps'][app]['vector'] for app in app_names_chunk]
    test_ys = [dataset['apps'][app]['malicious'] for app in app_names_chunk]

    prediction_diff = tf.subtract(tf.argmax(y,1), tf.argmax(y_,1))
    # calculate how often benign apps were thought to be malicious
    false_positive = tf.equal(prediction_diff, tf.constant(-1,shape=[len(test_ys)],dtype=tf.int64))
    # calculate how often malicious apps were thought to be benign
    false_negative = tf.equal(prediction_diff, tf.constant(1,shape=[len(test_ys)],dtype=tf.int64))
    # recalculate prediction accuracy
    correct_prediction = tf.equal(prediction_diff, tf.constant(0,shape=[len(test_ys)],dtype=tf.int64))

    false_positive_rate = tf.reduce_mean(tf.cast(false_positive, tf.float32))
    false_negative_rate = tf.reduce_mean(tf.cast(false_negative, tf.float32))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    print(sess.run(false_positive_rate, feed_dict={x: test_xs, y_: test_ys}))
    print(sess.run(false_negative_rate, feed_dict={x: test_xs, y_: test_ys}))
    print(sess.run(accuracy, feed_dict={x: test_xs, y_: test_ys}))
    print(str(len(malicious_app_names)))
    print(str(len(benign_app_names)))

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

if __name__=='__main__':
    main()
