# -*- coding: utf-8 -*-

import gym
import math
import numpy as np
from collections import deque
import matplotlib.pyplot as plt


import torch
import torch.nn as nn

from time import time

"""
Episode 139     Average Score: 89.25
Episode 140     Average Score: 89.48
Episode 141     Average Score: 89.57
Episode 142     Average Score: 89.61
Episode 143     Average Score: 89.60
Episode 144     Average Score: 89.64
Episode 145     Average Score: 89.66
Episode 146     Average Score: 89.66
Episode 147     Average Score: 90.83


"""


class Agent(nn.Module):
  def __init__(self, env, dev, h_size=16):
    super(Agent, self).__init__()
    self.env = env
    self.dev = dev
    # state, hidden layer, action sizes
    self.s_size = env.observation_space.shape[0]
    self.h_size = h_size
    self.a_size = env.action_space.shape[0]
    # define layers
    self.fc1 = nn.Linear(self.s_size, self.h_size)
    self.fc2 = nn.Linear(self.h_size, self.a_size)
    self.tanh = nn.Tanh()
    self.relu = nn.ReLU()
    if device.type == 'cuda':
      self.cuda(device)
    print("Agent init on device {}".format(self.dev))
      
  def set_weights(self, weights):
    assert weights.size == self.get_weights_dim()
    s_size = self.s_size
    h_size = self.h_size
    a_size = self.a_size
    # separate the weights for each layer
    fc1_end = (s_size*h_size)+h_size
    fc1_W = torch.from_numpy(weights[:s_size*h_size].reshape(s_size, h_size))
    fc1_b = torch.from_numpy(weights[s_size*h_size:fc1_end])
    fc2_W = torch.from_numpy(weights[fc1_end:fc1_end+(h_size*a_size)].reshape(h_size, a_size))
    fc2_b = torch.from_numpy(weights[fc1_end+(h_size*a_size):])
    # set the weights for each layer
    self.fc1.weight.data.copy_(fc1_W.view_as(self.fc1.weight.data))
    self.fc1.bias.data.copy_(fc1_b.view_as(self.fc1.bias.data))
    self.fc2.weight.data.copy_(fc2_W.view_as(self.fc2.weight.data))
    self.fc2.bias.data.copy_(fc2_b.view_as(self.fc2.bias.data))
    
  
  def get_weights_dim(self):
    return (self.s_size+1)*self.h_size + (self.h_size+1)*self.a_size
      
  def forward(self, x):
    x = self.relu(self.fc1(x))
    x = self.tanh(self.fc2(x)) 
    # we generate the numpy as no optimization per-se will be done
    return x.cpu().data 
      
  def evaluate(self, weights, gamma=1.0, max_t=5000):
    self.set_weights(weights)
    episode_return = 0.0
    state = self.env.reset()
    nr_steps = np.inf
    for t in range(max_t):
      state = torch.from_numpy(state).float().to(self.dev)
      action = self.forward(state)
      state, reward, done, _ = self.env.step(action)
      episode_return += reward * math.pow(gamma, t)
      if done:
        nr_steps = t
        break
    return episode_return, nr_steps
  
def crossentropy_method(env, agent, n_iterations=500, max_t=1000, gamma=1.0, 
                        print_every=1, pop_size=50, elite_frac=0.2, sigma=0.5):
  """PyTorch implementation of a cross-entropy method.
      
  Params
  ======
      env: the environment
      agent: the agent
      n_iterations (int): maximum number of training iterations
      max_t (int): maximum number of timesteps per episode
      gamma (float): discount rate
      print_every (int): how often to print average score (over last 100 episodes)
      pop_size (int): size of population at each iteration
      elite_frac (float): percentage of top performers to use in update
      sigma (float): standard deviation of additive noise
  """
  n_elite=int(pop_size*elite_frac)

  scores_deque = deque(maxlen=100)
  scores = []
  best_weight = sigma*np.random.randn(agent.get_weights_dim())
  
  print("Starting cross-entropy method training...")
  
  best_scores = -np.inf
  t_start = time()
  for i_iteration in range(1, n_iterations+1):
    t_0 = time()
    weights_pop = [best_weight + (sigma*np.random.randn(agent.get_weights_dim())) for i in range(pop_size)]
    rewards = np.array([agent.evaluate(weights, gamma, max_t)[0] for weights in weights_pop])

    elite_idxs = rewards.argsort()[-n_elite:]
    elite_weights = [weights_pop[i] for i in elite_idxs]
    best_weight = np.array(elite_weights).mean(axis=0)

    reward, nr_steps = agent.evaluate(best_weight, gamma=1.0)
    scores_deque.append(reward)
    scores.append(reward)
    
    t_1 = time()
    
    mean_scores = np.mean(scores_deque)
    if mean_scores > best_scores:      
      best_scores = mean_scores
      torch.save(agent.state_dict(), 'checkpoint.pth')
      
    
    if i_iteration % print_every == 0:
        print('Episode {}\tAverage Score: {:>5.2f}  Time: {:.1f}s'.format(
            i_iteration, np.mean(scores_deque), t_1-t_0))

    if mean_scores>=90.0:
        print('\nEnvironment solved in {:d} iterations!\tAverage Score: {:.2f}'.format(
            i_iteration-100, np.mean(scores_deque)))
        break
  t_end = time()
  print("Training done in {:.1f} min".format((t_end-t_start)/60))
  return scores, i_iteration



gpu_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
cpu_device = torch.device("cpu")

device = cpu_device

env = gym.make('MountainCarContinuous-v0')
env.seed(101)
np.random.seed(101)

print('observation space:', env.observation_space)
print('action space:', env.action_space)
print('  - low:', env.action_space.low)
print('  - high:', env.action_space.high)


agent = Agent(env=env, dev=device)
scores, nr_steps = crossentropy_method(env=env, agent=agent)

fig = plt.figure()
ax = fig.add_subplot(111)
plt.plot(np.arange(1, len(scores)+1), scores)
plt.ylabel('Score')
plt.xlabel('Episode #')
plt.show()
