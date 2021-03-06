import matplotlib.pyplot as plt
import numpy as np
from numpy import matlib as mb
from pathlib import Path
import time
import random
import math
from tqdm import tqdm

K = 10
dimension_d = 3072
exp_derivative = 1e-6
eta_min = 1e-5
eta_max = 1e-1
# n_s = 400 # 2 * math.floor(10000 // 100) # 800   # Step size
# n_s = 2 * math.floor(45000 // 100)  # Step size
n_s = 2 * math.floor(49000 // 100)  # Step size

# Number of nodes of the hidden layer
m = 50

def unpickle(file):
    import pickle
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict

def get_one_hot(index, array_size = 10):
    one_hot = [0] * array_size
    one_hot[index] = 1
    return one_hot


def display_imgs(file):
    global K, d
    batch_data = unpickle(file)
    X, Y, y = [], [], []
    for i, img in enumerate(batch_data[b"data"]):
        reshaped_img = np.transpose(np.reshape(img, (3, 32, 32)), (1, 2, 0))
        plt.imshow(reshaped_img)


def read_imgs(file):
    global K
    batch_data = unpickle(file)
    X = np.array(normalize_distribution(batch_data[b"data"].T))
    y = np.array(batch_data[b"labels"])
    Y = np.array(np.eye(K)[y].T)
    return X, Y, y


def read_multiple_batches(files):
    global K
    X = None
    y = None
    Y = None
    for i, file in enumerate(files):
        temp_X, temp_Y, temp_y = read_imgs(file)
        if i == 0:
            X = temp_X
            Y = temp_Y
            y = temp_y
        else:    
            X = np.concatenate((X, temp_X), axis=1)
            y = np.concatenate((y, temp_y), axis=0)
            Y = np.concatenate((Y, temp_Y), axis=1)
        
    return X, Y, y

def normalize_distribution(X):
    mean_X = np.mean(X, axis=0)
    std_X = np.std(X, axis=0)
    X = (X - mean_X) / std_X
    return X

def initialize_parameters_layer_1(W_rows, W_cols, b_rows):
    global dimension_d, m
    np.random.seed(400)
    W = np.random.normal(loc = 0.0, scale = (1 / np.sqrt(dimension_d)), size = (W_rows, W_cols))
    b = np.zeros((b_rows, 1))
    return W, b

def initialize_parameters_hidden_layer(W_rows, W_cols, b_rows):
    global m
    np.random.seed(400)
    W = np.random.normal(loc = 0.0, scale = (1 / np.sqrt(m)), size = (W_rows, W_cols))
    b = np.zeros((b_rows, 1))
    return W, b

def softmax(s):
    """
    Activation function that turns our probabilites into values summing to 1.
    Returns all new values for the probabilities.
    """
    e_x = np.exp(s - np.max(s))
    return e_x / e_x.sum(axis=0)

def predict_outputs(X, W_1, b_1, W_2, b_2):
    """
    X: input data
    W_1: weights for each input data point
    b_1: bias parameter for the inputs
    W_2: weights for each node in the hidden layer
    b_2: bias parameter for the hidden layer
    Get the outputs (Y) for the classifier.
    return: H, P
    """
    # Scores from input layer
    s1 = np.dot(W_1, X) + b_1
    # Applying ReLu activation function for getting hidden ouput from 1st layer
    H = np.maximum(s1, 0, s1)
    # Scores from hidden layer
    s = np.dot(W_2, H) + b_2
    # Applying softmax activation function for output from hidden layer
    P = softmax(s)
    return H, P

def compute_loss(X, Y, W_1, b_1, W_2, b_2, lambda_value):
    """
    Computes the cross-entropy loss of the NN.
    It uses the cross-entropy formulae for each input as well as a
    regularization term.
    """
    H, P = predict_outputs(X, W_1, b_1, W_2, b_2)

    cross_entropy_loss = (-1 / X.shape[1]) * np.sum(
        [np.log(np.dot(Y[:, index].T, P[:, index])) for index in range(X.shape[1])]
    )

    regularization_W1 = lambda_value * np.sum(np.square(W_1))
    regularization_W2 = lambda_value * np.sum(np.square(W_2))
    total_loss = cross_entropy_loss + regularization_W1 + regularization_W2

    return total_loss
    

def compute_accuracy(X, y, W_1, b_1, W_2, b_2):
    """
    Computes the accuracy of the classifier for a given set of examples:
    percentage of examples for which it gets the correct answer.
    - Each column of X corresponds to an image and X has size dxn.
    - y is the vector of ground truth labels of length n.
    - acc is a scalar value containing the accuracy.
    k ∗ = arg max {p1, ..., pK}
    """
    H, P = predict_outputs(X, W_1, b_1, W_2, b_2)

    # Returns the column-index of the max value within each row of P (predicted scores)
    pred_class_labels = np.argmax(P, axis=0)
    # print('Predicted outputs', pred_class_labels)
    # Computes and returns the percentage of correctly predicted labels
    return np.mean(pred_class_labels == y) * 100


def compute_gradient(X, Y, H, P, W_1, b_1, W_2, b_2, lambda_value):
    """
    -each column of X corresponds to an image and it has size d×n.
    -each colum of H corresponds to a score from the hidden layer.
    -each column of Y (K×n) is the one-hot ground truth label for the cor-
    responding column of X.
    -each column of P contains the probability for each label for the image
    in the corresponding column of X. P has size K×n.
    -grad_W1 is the gradient matrix of the cost J relative to W1 and has size
    m×d. Also called dw.
    -grad_b1 is the gradient vector of the cost J relative to b1 and has size
    m×1.
    -grad_W2 is the gradient matrix of the cost J relative to W2 and has size
    K×m. Also called dw.
    -grad_b2 is the gradient vector of the cost J relative to b2 and has size
    K×1.
    """
    n_batch = X.shape[1]
    # Initializing gradients for layer 1
    grad_W1 = np.zeros(W_1.shape)
    grad_b1 = np.zeros(b_1.shape)
    # Initializing gradients for hidden layer
    grad_W2 = np.zeros(W_2.shape)
    grad_b2 = np.zeros(b_2.shape)

    average_param = 1 / n_batch

    ##### Gradients from the output layer to the scores of the hidden layer #####
    # Gbatch (scores 2, dz_hidden)
    G_batch = -(Y - P)
    # Computing gradient of J with respect to W2
    grad_W2 = average_param * np.dot(G_batch, H.T)
    # Add regularization parameter
    grad_W2 += 2 * lambda_value * W_2
    # Computing gradient of J with respect to bias b2
    grad_b2 = average_param * np.dot(G_batch, np.ones((n_batch, 1)))
    ##########
    ##########

    ##### Gradients from the hidden layer to the scores of the input layer #####
    # Back-propagating gradients throughout the hidden layer
    G_batch = np.dot(W_2.T, G_batch)    # Because s = W2 * H + b2 and ds/dh = W2
    # Gbatch (scores 1, dz_0)
    G_batch = G_batch * np.int8(H > 0)   # Because h = max(0, s1) and dh/ds1 = diag(Ind(s1 > 0))
    # Computing gradient of J with respect to W1
    grad_W1 = average_param * np.dot(G_batch, X.T)
    # Add regularization parameter
    grad_W1 += 2 * lambda_value * W_1
    # Computing gradient of J with respect to bias b1
    grad_b1 = average_param * np.dot(G_batch, np.ones((n_batch, 1)))
    ##########
    ##########

    return grad_W1, grad_b1, grad_W2, grad_b2


def ComputeGradsNumSlow(X, Y, P, W_1, b_1, W_2, b_2, lambda_value, h):
    """ Converted from matlab code by Andree Hultgren """
    no = W_1.shape[0]
    d = X.shape[0]
    no_2 = W_2.shape[0]

    grad_W1 = np.zeros(W_1.shape)
    grad_b1 = np.zeros((no, 1))
    grad_W2 = np.zeros(W_2.shape)
    grad_b2 = np.zeros((no_2, 1))
	
    for i in range(len(b_1)):
        b_try = np.array(b_1)
        b_try[i] -= h

        c1 = compute_loss(X, Y, W_1, b_try, W_2, b_2, lambda_value)

        b_try = np.array(b_1)
        b_try[i] += h
        c2 = compute_loss(X, Y, W_1, b_try, W_2, b_2, lambda_value)

        grad_b1[i] = (c2-c1) / (2*h)

    for i in range(len(b_2)):
        b_try = np.array(b_2)
        b_try[i] -= h

        c1 = compute_loss(X, Y, W_1, b_1, W_2, b_try, lambda_value)

        b_try = np.array(b_2)
        b_try[i] += h
        c2 = compute_loss(X, Y, W_1, b_1, W_2, b_try, lambda_value)

        grad_b2[i] = (c2-c1) / (2*h)

    for i in range(W_1.shape[0]):
        for j in range(W_1.shape[1]):
            W_try = np.array(W_1)
            W_try[i,j] -= h
            c1 = compute_loss(X, Y, W_try, b_1, W_2, b_2, lambda_value)

            W_try = np.array(W_1)
            W_try[i,j] += h
            c2 = compute_loss(X, Y, W_try, b_1, W_2, b_2, lambda_value)

            grad_W1[i,j] = (c2-c1) / (2*h)
            
    for i in range(W_2.shape[0]):
        for j in range(W_2.shape[1]):
            W_try = np.array(W_2)
            W_try[i,j] -= h
            c1 = compute_loss(X, Y, W_1, b_1, W_try, b_2, lambda_value)

            W_try = np.array(W_2)
            W_try[i,j] += h
            c2 = compute_loss(X, Y, W_1, b_1, W_try, b_2, lambda_value)

            grad_W2[i,j] = (c2-c1) / (2*h)

    return grad_W1, grad_b1, grad_W2, grad_b2

def ComputeGradsNum(X, Y, P, W_1, b_1, W_2, b_2, lambda_value, h):
    """ Converted from matlab code by Andree Hultgren """
    no = W_1.shape[0]
    d = X.shape[0]
    no_2 = W_2.shape[0]

    grad_W1 = np.zeros(W_1.shape)
    grad_b1 = np.zeros((no, 1))
    grad_W2 = np.zeros(W_2.shape)
    grad_b2 = np.zeros((no_2, 1))

    c = compute_loss(X, Y, W_1, b_1, W_2, b_2, lambda_value)
	
    for i in range(len(b_1)):
        b_try = np.array(b_1)
        b_try[i] += h
        c2 = compute_loss(X, Y, W_1, b_try, W_2, b_2, lambda_value)
        grad_b1[i] = (c2-c) / h
    
    for i in range(len(b_2)):
        b_try = np.array(b_2)
        b_try[i] += h
        c2 = compute_loss(X, Y, W_1, b_1, W_2, b_try, lambda_value)
        grad_b2[i] = (c2-c) / h

    for i in range(W_1.shape[0]):
        for j in range(W_1.shape[1]):
            W_try = np.array(W_1)
            W_try[i,j] += h
            c2 = compute_loss(X, Y, W_try, b_1, W_2, b_2, lambda_value)
            grad_W1[i,j] = (c2-c) / h
            
    for i in range(W_2.shape[0]):
        for j in range(W_2.shape[1]):
            W_try = np.array(W_2)
            W_try[i,j] += h
            c2 = compute_loss(X, Y, W_1, b_1, W_try, b_2, lambda_value)
            grad_W2[i,j] = (c2-c) / h

    return grad_W1, grad_b1, grad_W2, grad_b2

def grad_checking(dw, dw_num, db, db_num):
    global exp_derivative
    check_dW = ( np.abs(dw[0, 0] - dw_num[0, 0]) ) / ( max(exp_derivative, np.abs(dw[0, 0]) + np.abs(dw_num[0, 0])) )
    check_db = ( np.abs(db[0, 0] - db_num[0, 0]) ) / ( max(exp_derivative, np.abs(db[0, 0]) + np.abs(db_num[0, 0])) )
    print('Check dW: ', check_dW)
    print('Check db: ', check_db)
    return check_dW < exp_derivative and check_db < exp_derivative


def create_mini_batches(X_train, Y_train, n_batch):

    indexes = np.random.permutation(X_train.shape[1])
    X_train = X_train[:, indexes]
    Y_train = Y_train[:, indexes]
    mini_batches = []
    for i in range(0, X_train.shape[1], n_batch):
        X_batch = X_train[:, i:i + n_batch]
        Y_batch = Y_train[:, i:i + n_batch]
        mini_batches.append((X_batch, Y_batch))
    return mini_batches

def calculate_learning_rate(t_step, l_cycle = 0):
    """
    Computes and returns the updated value for the eta parameter
    in cycling learning rate strategy.
    """
    if t_step > n_s:
        eta_update = eta_max - ((t_step - (2 * l_cycle + 1) * n_s) / n_s) * (eta_max - eta_min)
    else:
        eta_update = eta_min + ((t_step - 2 * l_cycle * n_s) / n_s) * (eta_max - eta_min)
    
    return eta_update

def minibatch_gradient_descent(X, Y, y_labels, \
    X_val, Y_val, y_val_labels, GD_params, W_1, b_1, W_2, b_2, lambda_value):
    
    global n_s
    # GD_params: dictionary
    n_batch = GD_params['n_batch']   # Size of the mini-batches.
    loss_history = []
    loss_history_validation = []
    accuracy_history = []
    accuracy_history_validation = []
    n_epochs = []
    l_cycles = GD_params['l_cycles'] or 1
    eta_vals = []
    
    # One step is half of a cycle (one cycle = 2 steps, total cycles = l_steps / 2)
    total_update_steps = 0
    accumulated_t = 0
    for l in tqdm(range(l_cycles)): # L = l0, l1, l2
        t = 0   # t is every step where we are at
        while t < (2 * n_s):
            mini_batches = create_mini_batches(X, Y, n_batch)
            for mini_batch in mini_batches:
                eta_in_step = calculate_learning_rate(t)
                X_mini, Y_mini = mini_batch
                H, P = predict_outputs(X_mini, W_1, b_1, W_2, b_2)
                dW_1, db_1, dW_2, db_2 = compute_gradient(X_mini, Y_mini, H, P, \
                    W_1, b_1, W_2, b_2, lambda_value)
                W_1 -= eta_in_step * dW_1
                b_1 -= eta_in_step * db_1
                W_2 -= eta_in_step * dW_2
                b_2 -= eta_in_step * db_2
                # Move to the next step
                t += 1
                accumulated_t += 1
                eta_vals.append(eta_in_step)
            
            loss = compute_loss(X, Y, W_1, b_1, W_2, b_2, lambda_value)
            loss_val = compute_loss(X_val, Y_val, W_1, b_1, W_2, b_2, lambda_value)
            
            accuracy = compute_accuracy(X, y_labels, W_1, b_1, W_2, b_2)
            accuracy_val = compute_accuracy(X_val, y_val_labels, W_1, b_1, W_2, b_2)
            
            loss_history.append(loss)
            loss_history_validation.append(loss_val)
            accuracy_history.append(accuracy)
            accuracy_history_validation.append(accuracy_val)
            
            n_epochs.append(accumulated_t)
            
        total_update_steps += t
    
    # Plot the schedule
    plot_cyclic_rate(range(1, total_update_steps + 1), eta_vals)
    
    return n_epochs, loss_history, loss_history_validation, accuracy_history, \
        accuracy_history_validation, W_1, b_1, W_2, b_2

def plot_cyclic_rate(update_steps, eta_vals):
    fig, ax1 = plt.subplots()
    ax1.plot(update_steps, eta_vals, label='')
    ax1.set(xlabel='Update step', ylabel='LR (η)', title='CLR Schedule')
    ax1.grid()
    plt.show()

def plot_loss(update_steps, loss_history_train, loss_history_val, 
    accuracy_history_train, accuracy_history_val):
    
    fig, (ax1, ax2) = plt.subplots(1, 2)
    
    if loss_history_train:
        ax1.plot(update_steps, loss_history_train, label='Training set')
    if loss_history_val:
        ax1.plot(update_steps, loss_history_val, label='Validation set')
    if accuracy_history_train:
        ax2.plot(update_steps, accuracy_history_train, label='Training set')
    if accuracy_history_val:
        ax2.plot(update_steps, accuracy_history_val, label='Validation set')

    fig.suptitle('2-Layer NN Performance', x=0.25)
    ax1.set(xlabel='Update step', ylabel='Loss', title='Loss')
    ax1.grid()
    ax2.set(xlabel='Update step', ylabel='Accuracy', title='Accuracy')
    ax2.grid()

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center')
    fig.savefig('imgs/graph_task_3.png')
    plt.show()


def plot_learnt_weight_matrix(W):
    global K
    class_templates = []
    class_labels = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
    for i in range(W.shape[0]):
        plt.subplot(2, 5, i + 1)
        img = np.transpose(np.reshape(W[i, :], (3, 32, 32)), (1, 2, 0))
        img = (img - img.min()) / (img.max() - img.min())
        class_templates.append(img)
        plt.axis('off')
        plt.imshow(img)
        plt.title(class_labels[i])
    # Plot big-sized labeled images
    plt.suptitle('Weigth Matrix Templates')
    plt.savefig('imgs/labeled_templates_case_4.png')
    plt.show()
    # Plot all images concatenated
    plt.title('Weigth Matrix Templates')
    plt.imshow(np.concatenate(tuple(class_templates), axis=1))
    plt.axis('off')
    plt.savefig('imgs/templates_case_4.png')
    plt.show()


def build_classification_model(coarse_search=False, full_training=False):
    
    # l_min, l_max = -5, -1
    l_min, l_max = -4, -3
    GD_params = {'n_batch': 100, 'l_cycles': 3}
    num_tries = 1
    best_accuracy = 0
    best_lr = 0
    best_try = 1
    
    if coarse_search:
        num_tries = 8
    else:
        # GD_params['lambda'] = .01
        # Best lambda for regularization:
        GD_params['lambda'] = 9.682569422890101e-4
        
    for try_step in range(num_tries):
        if coarse_search:
            l = l_min + (l_max - l_min) * random.random()
            GD_params['lambda'] = 10**l
        validation_accuracy, testing_accuracy = train_nn(GD_params, full_training=full_training)
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            best_lr = GD_params['lambda']
            best_try = try_step + 1
        print('------ Try #', try_step + 1, '------', 'λ =', GD_params['lambda'])
        print('Final Accuracy in Validation:', validation_accuracy)
        print('Final Accuracy in Testing:', testing_accuracy, end='\n\n')
        
    print('Best LR Value:', best_lr, 'Accuracy:', best_accuracy, '- Try #', best_try)

def assemble_datasets():
    global dimension_d
    
    data_path = '../datasets/cifar-10-batches-py/'
    batch_file_training = data_path + 'data_batch_1'
    batch_file_validation = data_path + 'data_batch_2'
    batch_file_test = data_path + 'test_batch'
    num_data = 10000

    # Reading training set
    X_train, Y_train, y_train = read_imgs(batch_file_training)
    X_train = X_train[:dimension_d, :num_data]
    Y_train = Y_train[:, :num_data]
    y_train = y_train[:num_data]

    # Reading validation set
    X_val, Y_val, y_val = read_imgs(batch_file_validation)
    X_val = X_val[:, :num_data]
    Y_val = Y_val[:, :num_data]
    y_val = y_val[:num_data]

    # Reading test set
    X_test, Y_test, y_test = read_imgs(batch_file_test)
    
    return ((X_train, Y_train, y_train), (X_val, Y_val, y_val), (X_test, Y_test, y_test))


def assemble_datasets_real_training():
    """
    Load datasets for a full training process.
    It includes 5 training batches and a subset of 5000 images for validation.
    """
    global dimension_d
    
    data_path = '../datasets/cifar-10-batches-py/'
    batch_file_training_1 = data_path + 'data_batch_1'
    batch_file_training_2 = data_path + 'data_batch_2'
    batch_file_training_3 = data_path + 'data_batch_3'
    batch_file_training_4 = data_path + 'data_batch_4'
    batch_file_training_5 = data_path + 'data_batch_5'
    batch_file_test = data_path + 'test_batch'
    num_data = 10000
    split_limit = 1000 # 5000

    # Reading training set
    X_train_full, Y_train_full, y_train_full = read_multiple_batches([
        batch_file_training_1, 
        batch_file_training_2, 
        batch_file_training_3, 
        batch_file_training_4, 
        batch_file_training_5
        ])
    
    num_data = X_train_full.shape[1] - split_limit
    
    X_train = X_train_full[:dimension_d, :num_data]
    Y_train = Y_train_full[:, :num_data]
    y_train = y_train_full[:num_data]

    # Reading validation set
    X_val = X_train_full[:, num_data:]
    Y_val = Y_train_full[:, num_data:]
    y_val = y_train_full[num_data:]

    # Reading test set
    X_test, Y_test, y_test = read_imgs(batch_file_test)
    
    return ((X_train, Y_train, y_train), (X_val, Y_val, y_val), (X_test, Y_test, y_test))


def train_nn(GD_params, full_training=False):
    global dimension_d, K, m
    
    # Organizing the data sets
    if full_training:
        train_data, validation_data, test_data = assemble_datasets_real_training()
    else:
        train_data, validation_data, test_data = assemble_datasets()
    
    # Initializing parameters
    W_1, b_1 = initialize_parameters_layer_1(m, dimension_d, m)
    W_2, b_2 = initialize_parameters_hidden_layer(K, m, K)

    init_time = time.time()

    # Training
    n_epochs_train, loss_history_train, loss_history_val, \
    accuracy_history_train, accuracy_history_val, \
    W1_star, b1_star, W2_star, b2_star = \
        minibatch_gradient_descent(
            *train_data, *validation_data, \
                GD_params, W_1, b_1, W_2, b_2, GD_params['lambda']
            )
    # End of training
    
    # final_time = time.time()
    
    # ########## Block for Final Validation and Testing ##########
    # #
    validation_accuracy = compute_accuracy(validation_data[0], validation_data[2], W1_star, b1_star, W2_star, b2_star)
    testing_accuracy = compute_accuracy(test_data[0], test_data[2], W1_star, b1_star, W2_star, b2_star)
    #
    ########## End of Testing ##########
    
    # print('Time for training:', final_time - init_time, 'sec')
    print('Training -> ', 'Initial Loss: ', loss_history_train[0], 'Final Loss: ',
        loss_history_train[-1], 'Accuracy: ', accuracy_history_train[-1])

    plot_loss(n_epochs_train, loss_history_train, loss_history_val, accuracy_history_train, 
              accuracy_history_val)

    # print('Final Accuracy in Validation: ', validation_accuracy)
    # print('Final Accuracy in Testing: ', testing_accuracy)
    
    return validation_accuracy, testing_accuracy

def model_gradient_checking():
    global exp_derivative, dimension_d, K, m
    
    # Reading datasets
    train_data, validation_data, test_data = assemble_datasets()
    X_train = train_data[0]
    Y_train = train_data[1]
    
    # Initializing parameters
    W_1, b_1 = initialize_parameters_layer_1(m, dimension_d, m)
    W_2, b_2 = initialize_parameters_hidden_layer(K, m, K)
    
    GD_params = {'lambda': 0.001}
    
    ########## Block for Gradient Checking ##########
    #
    H, P = predict_outputs(X_train, W_1, b_1, W_2, b_2)
    
    dW_1, db_1, dW_2, db_2 = compute_gradient(X_train, Y_train, H, P, \
        W_1, b_1, W_2, b_2, GD_params['lambda'])
    
    dW1_center_diff, db1_center_diff, dW2_center_diff, db2_center_diff = ComputeGradsNumSlow(X_train, \
        Y_train, P, W_1, b_1, W_2, b_2, GD_params['lambda'], exp_derivative)
    
    dW1_finite, db1_finite, dW2_finite, db2_finite = ComputeGradsNum(X_train, \
        Y_train, P, W_1, b_1, W_2, b_2, GD_params['lambda'], exp_derivative)

    print('Analytical vs Centered Difference W1, B1:', grad_checking(dW_1, dW1_center_diff, db_1, db1_center_diff))
    print('Analytical vs Centered Difference W2, B2:', grad_checking(dW_2, dW2_center_diff, db_2, db2_center_diff))
    
    print('Analytical vs Finite Difference W1, B1:', grad_checking(dW_1, dW1_finite, db_1, db1_finite))
    print('Analytical vs Finite Difference W2, B2:', grad_checking(dW_2, dW2_finite, db_2, db2_finite))
    
    ########## End of Gradient Checking ##########
    

if __name__ == "__main__":
    
    # Initializing NN models
    build_classification_model(full_training=True)
    
    # model_gradient_checking()

    # plot_learnt_weight_matrix(W_star)
