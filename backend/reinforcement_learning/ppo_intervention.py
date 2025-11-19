"""
Reinforcement Learning for Optimal Intervention Planning.

Uses PPO (Proximal Policy Optimization) to learn intervention sequences
that maximize causal effect while minimizing cost.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import deque


class InterventionEnvironment:
    """
    Environment for intervention planning.
    
    State: Current causal graph + intervention history
    Action: Select next intervention (node to intervene on)
    Reward: Causal effect improvement - intervention cost
    """
    
    def __init__(
        self,
        num_nodes: int,
        causal_graph: torch.Tensor,
        target_node: int,
        intervention_costs: Optional[torch.Tensor] = None
    ):
        """
        Initialize environment.
        
        Args:
            num_nodes: Number of nodes in causal graph
            causal_graph: [N, N] adjacency matrix
            target_node: Index of target outcome node
            intervention_costs: [N] cost per intervention (default: uniform)
        """
        self.num_nodes = num_nodes
        self.original_graph = causal_graph.clone()
        self.current_graph = causal_graph.clone()
        self.target_node = target_node
        
        if intervention_costs is None:
            self.intervention_costs = torch.ones(num_nodes)
        else:
            self.intervention_costs = intervention_costs
        
        self.intervention_history = []
        self.current_effect = 0.0
        self.max_steps = num_nodes  # Maximum interventions
        self.step_count = 0
    
    def reset(self) -> torch.Tensor:
        """Reset environment to initial state."""
        self.current_graph = self.original_graph.clone()
        self.intervention_history = []
        self.current_effect = 0.0
        self.step_count = 0
        return self._get_state()
    
    def _get_state(self) -> torch.Tensor:
        """
        Get current state representation.
        
        Returns:
            State tensor [num_nodes * num_nodes + num_nodes]
        """
        # Flatten graph
        graph_flat = self.current_graph.flatten()
        
        # Intervention mask (which nodes intervened)
        intervention_mask = torch.zeros(self.num_nodes)
        for node_idx in self.intervention_history:
            intervention_mask[node_idx] = 1.0
        
        # Concatenate
        state = torch.cat([graph_flat, intervention_mask])
        
        return state
    
    def step(self, action: int) -> Tuple[torch.Tensor, float, bool, Dict]:
        """
        Take intervention action.
        
        Args:
            action: Node index to intervene on
            
        Returns:
            Tuple of (next_state, reward, done, info)
        """
        # Check if already intervened
        if action in self.intervention_history:
            reward = -10.0  # Penalty for repeating intervention
            done = False
            return self._get_state(), reward, done, {'invalid_action': True}
        
        # Perform intervention (set node to fixed value, remove incoming edges)
        self.current_graph[:, action] = 0.0
        self.intervention_history.append(action)
        
        # Compute causal effect (simplified: path strength to target)
        new_effect = self._compute_causal_effect(action)
        
        # Reward: improvement in effect - cost
        effect_improvement = new_effect - self.current_effect
        cost = self.intervention_costs[action].item()
        reward = effect_improvement - cost * 0.1
        
        self.current_effect = new_effect
        self.step_count += 1
        
        # Done if reached max steps or no more valid actions
        done = (self.step_count >= self.max_steps) or (len(self.intervention_history) == self.num_nodes)
        
        return self._get_state(), reward, done, {
            'effect': new_effect,
            'cost': cost,
            'intervention_count': len(self.intervention_history)
        }
    
    def _compute_causal_effect(self, intervention_node: int) -> float:
        """
        Compute causal effect of intervention on target.
        
        Simplified: sum of path strengths from intervention to target.
        """
        # Use graph powers to find paths
        paths = torch.matrix_power(self.current_graph, self.max_steps)
        effect = paths[intervention_node, self.target_node].item()
        
        # Add direct effect bonus
        if self.current_graph[intervention_node, self.target_node] > 0:
            effect += self.current_graph[intervention_node, self.target_node].item() * 2
        
        return effect


class PolicyNetwork(nn.Module):
    """Policy network for selecting interventions."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            state: [B, state_dim]
            
        Returns:
            Action logits [B, action_dim]
        """
        return self.network(state)
    
    def get_action(self, state: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[int, torch.Tensor, torch.Tensor]:
        """
        Sample action from policy.
        
        Args:
            state: State tensor
            mask: Binary mask for invalid actions
            
        Returns:
            Tuple of (action, log_prob, entropy)
        """
        logits = self.forward(state.unsqueeze(0))
        
        # Apply mask
        if mask is not None:
            logits = logits.masked_fill(mask.unsqueeze(0) == 0, float('-inf'))
        
        # Sample action
        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action.item(), log_prob, entropy


class ValueNetwork(nn.Module):
    """Value network for estimating state value."""
    
    def __init__(self, state_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            state: [B, state_dim]
            
        Returns:
            State value [B, 1]
        """
        return self.network(state)


class PPOAgent:
    """Proximal Policy Optimization agent."""
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01
    ):
        """
        Initialize PPO agent.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension (number of nodes)
            hidden_dim: Hidden layer dimension
            lr: Learning rate
            gamma: Discount factor
            gae_lambda: GAE lambda for advantage estimation
            clip_epsilon: PPO clip parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy bonus coefficient
        """
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        
        # Networks
        self.policy = PolicyNetwork(state_dim, action_dim, hidden_dim)
        self.value = ValueNetwork(state_dim, hidden_dim)
        
        # Optimizer
        self.optimizer = torch.optim.Adam(
            list(self.policy.parameters()) + list(self.value.parameters()),
            lr=lr
        )
        
        # Experience buffer
        self.buffer = {
            'states': [],
            'actions': [],
            'rewards': [],
            'log_probs': [],
            'values': [],
            'dones': []
        }
    
    def select_action(self, state: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[int, Dict]:
        """Select action using current policy."""
        self.policy.eval()
        self.value.eval()
        
        with torch.no_grad():
            action, log_prob, entropy = self.policy.get_action(state, mask)
            value = self.value(state.unsqueeze(0))
        
        return action, {
            'log_prob': log_prob,
            'value': value,
            'entropy': entropy
        }
    
    def store_transition(self, state, action, reward, log_prob, value, done):
        """Store transition in buffer."""
        self.buffer['states'].append(state)
        self.buffer['actions'].append(action)
        self.buffer['rewards'].append(reward)
        self.buffer['log_probs'].append(log_prob)
        self.buffer['values'].append(value)
        self.buffer['dones'].append(done)
    
    def compute_gae(self, rewards: List[float], values: List[torch.Tensor], dones: List[bool]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute Generalized Advantage Estimation.
        
        Returns:
            Tuple of (advantages, returns)
        """
        advantages = []
        gae = 0
        
        values = [v.item() for v in values]
        next_value = 0
        
        for t in reversed(range(len(rewards))):
            if dones[t]:
                next_value = 0
                gae = 0
            
            delta = rewards[t] + self.gamma * next_value - values[t]
            gae = delta + self.gamma * self.gae_lambda * gae
            
            advantages.insert(0, gae)
            next_value = values[t]
        
        advantages = torch.tensor(advantages)
        returns = advantages + torch.tensor(values)
        
        return advantages, returns
    
    def update(self, epochs: int = 4, batch_size: int = 64):
        """Update policy using PPO."""
        if len(self.buffer['states']) == 0:
            return {}
        
        # Compute advantages
        advantages, returns = self.compute_gae(
            self.buffer['rewards'],
            self.buffer['values'],
            self.buffer['dones']
        )
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Convert to tensors
        states = torch.stack(self.buffer['states'])
        actions = torch.tensor(self.buffer['actions'])
        old_log_probs = torch.stack(self.buffer['log_probs'])
        
        # Training
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy = 0
        
        dataset_size = len(states)
        indices = np.arange(dataset_size)
        
        for epoch in range(epochs):
            np.random.shuffle(indices)
            
            for start_idx in range(0, dataset_size, batch_size):
                batch_indices = indices[start_idx:start_idx + batch_size]
                
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                
                # Forward pass
                logits = self.policy(batch_states)
                values = self.value(batch_states).squeeze(-1)
                
                # Policy loss
                probs = F.softmax(logits, dim=-1)
                dist = torch.distributions.Categorical(probs)
                new_log_probs = dist.log_prob(batch_actions)
                entropy = dist.entropy().mean()
                
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # Value loss
                value_loss = F.mse_loss(values, batch_returns)
                
                # Total loss
                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    list(self.policy.parameters()) + list(self.value.parameters()),
                    max_norm=0.5
                )
                self.optimizer.step()
                
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.item()
        
        # Clear buffer
        for key in self.buffer:
            self.buffer[key] = []
        
        return {
            'policy_loss': total_policy_loss / (epochs * (dataset_size // batch_size)),
            'value_loss': total_value_loss / (epochs * (dataset_size // batch_size)),
            'entropy': total_entropy / (epochs * (dataset_size // batch_size))
        }


def train_rl_agent(
    agent: PPOAgent,
    env: InterventionEnvironment,
    num_episodes: int = 1000,
    max_steps_per_episode: int = 50
) -> List[float]:
    """
    Train RL agent.
    
    Args:
        agent: PPO agent
        env: Intervention environment
        num_episodes: Number of training episodes
        max_steps_per_episode: Max steps per episode
        
    Returns:
        List of episode returns
    """
    episode_returns = []
    
    for episode in range(num_episodes):
        state = env.reset()
        episode_return = 0
        
        for step in range(max_steps_per_episode):
            # Create action mask (valid actions)
            mask = torch.ones(env.num_nodes)
            for intervened_node in env.intervention_history:
                mask[intervened_node] = 0
            
            # Select action
            action, info = agent.select_action(state, mask)
            
            # Take step
            next_state, reward, done, step_info = env.step(action)
            
            # Store transition
            agent.store_transition(
                state, action, reward,
                info['log_prob'], info['value'], done
            )
            
            episode_return += reward
            state = next_state
            
            if done:
                break
        
        # Update agent
        if (episode + 1) % 10 == 0:
            metrics = agent.update()
            print(f"Episode {episode + 1}/{num_episodes} - Return: {episode_return:.2f} - " +
                  f"Policy Loss: {metrics.get('policy_loss', 0):.4f}")
        
        episode_returns.append(episode_return)
    
    return episode_returns


if __name__ == "__main__":
    print("✅ Reinforcement learning modules initialized")
    
    # Create dummy environment
    num_nodes = 10
    causal_graph = torch.rand(num_nodes, num_nodes) * 0.3
    causal_graph = (causal_graph > 0.7).float()  # Sparse graph
    
    env = InterventionEnvironment(
        num_nodes=num_nodes,
        causal_graph=causal_graph,
        target_node=9
    )
    
    # Create agent
    state_dim = num_nodes * num_nodes + num_nodes
    agent = PPOAgent(
        state_dim=state_dim,
        action_dim=num_nodes,
        hidden_dim=128
    )
    
    print(f"State dim: {state_dim}, Action dim: {num_nodes}")
    print("✅ RL agent ready for intervention planning!")
