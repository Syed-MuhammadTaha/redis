import threading
import time
import random
from typing import List, Optional, Dict
from enum import Enum
import logging

class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class ConsensusModule:
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.state = NodeState.FOLLOWER
        self.leader_id: Optional[str] = None
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        self.last_heartbeat = time.time()
        
        # Leader state
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
        # Configuration
        self.election_timeout_min = 150  # milliseconds
        self.election_timeout_max = 300  # milliseconds
        self.heartbeat_interval = 50  # milliseconds
        
        # Threading
        self.lock = threading.RLock()
        self.running = True
        self.election_timer = threading.Thread(target=self._run_election_timer)
        self.election_timer.daemon = True
        
        # Logging
        self.logger = logging.getLogger(f"consensus-{node_id}")

    def start(self):
        """Start the consensus module."""
        self.running = True
        self.election_timer.start()

    def stop(self):
        """Stop the consensus module."""
        self.running = False
        self.election_timer.join()

    def _run_election_timer(self):
        """Run the election timer loop."""
        while self.running:
            timeout = random.randint(self.election_timeout_min, self.election_timeout_max) / 1000
            time.sleep(0.01)  # Small sleep to prevent busy waiting
            
            with self.lock:
                if self.state == NodeState.LEADER:
                    continue
                
                if time.time() - self.last_heartbeat > timeout:
                    self._start_election()

    def _start_election(self):
        """Start a new election."""
        with self.lock:
            self.state = NodeState.CANDIDATE
            self.current_term += 1
            self.voted_for = self.node_id
            self.leader_id = None
            votes_received = 1  # Vote for self
            
            self.logger.info(f"Starting election for term {self.current_term}")
            
            # Request votes from all peers
            for peer in self.peers:
                try:
                    # In a real implementation, this would be an RPC call
                    # vote_granted = request_vote_rpc(peer, self.current_term, ...)
                    vote_granted = False  # Placeholder
                    if vote_granted:
                        votes_received += 1
                except Exception as e:
                    self.logger.error(f"Failed to request vote from {peer}: {e}")
            
            # Check if we won the election
            if votes_received > (len(self.peers) + 1) // 2:
                self._become_leader()
            else:
                self.state = NodeState.FOLLOWER

    def _become_leader(self):
        """Transition to leader state."""
        with self.lock:
            if self.state == NodeState.CANDIDATE:
                self.state = NodeState.LEADER
                self.leader_id = self.node_id
                
                # Initialize leader state
                for peer in self.peers:
                    self.next_index[peer] = self.commit_index + 1
                    self.match_index[peer] = 0
                
                self.logger.info(f"Node {self.node_id} became leader for term {self.current_term}")

    def handle_append_entries(self, term: int, leader_id: str) -> bool:
        """Handle append entries (heartbeat) from leader."""
        with self.lock:
            if term < self.current_term:
                return False
            
            if term > self.current_term:
                self.current_term = term
                self.state = NodeState.FOLLOWER
                self.voted_for = None
            
            self.last_heartbeat = time.time()
            self.leader_id = leader_id
            return True

    def handle_request_vote(self, candidate_id: str, term: int) -> bool:
        """Handle vote request from candidate."""
        with self.lock:
            if term < self.current_term:
                return False
            
            if term > self.current_term:
                self.current_term = term
                self.state = NodeState.FOLLOWER
                self.voted_for = None
            
            if (self.voted_for is None or self.voted_for == candidate_id):
                self.voted_for = candidate_id
                return True
            
            return False

    @property
    def is_leader(self) -> bool:
        """Check if this node is the leader."""
        return self.state == NodeState.LEADER 