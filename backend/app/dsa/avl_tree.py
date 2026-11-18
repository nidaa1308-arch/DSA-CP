"""
Self-Balancing AVL Tree Implementation.
Provides guaranteed O(log n) search, insertion, and deletion.
Supports deterministic duplicate keys and dynamic ordering for sweep-line status structures.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Generator, Iterator, Optional


@dataclass
class AVLNode:
    key: float
    value: Any
    height: int = 1
    left: Optional[AVLNode] = None
    right: Optional[AVLNode] = None

    @property
    def balance(self) -> int:
        lh = self.left.height if self.left else 0
        rh = self.right.height if self.right else 0
        return lh - rh

    def update_height(self) -> None:
        lh = self.left.height if self.left else 0
        rh = self.right.height if self.right else 0
        self.height = 1 + max(lh, rh)


class AVLTree:
    """
    Self-balancing AVL tree.
    Supports:
      - insert(key, value)
      - delete(key, value)
      - find(key, value)
      - predecessor(key, value)
      - successor(key, value)
      - inorder() / iterators
      - custom comparator or tie-breaker for duplicate / moving keys
    """

    def __init__(self, key_comparator: Optional[Callable[[float, Any, float, Any], int]] = None):
        """
        :param key_comparator: Optional function (k1, v1, k2, v2) -> int:
                               negative if (k1, v1) < (k2, v2),
                               0 if equal,
                               positive if (k1, v1) > (k2, v2).
        """
        self.root: Optional[AVLNode] = None
        self._size: int = 0
        self.comparator = key_comparator or self._default_compare

    @staticmethod
    def _default_compare(k1: float, v1: Any, k2: float, v2: Any) -> int:
        if abs(k1 - k2) > 1e-12:
            return -1 if k1 < k2 else 1
        # Deterministic secondary tie-breaker using repr / str or hash
        s1 = str(v1)
        s2 = str(v2)
        if s1 != s2:
            return -1 if s1 < s2 else 1
        i1 = id(v1)
        i2 = id(v2)
        if i1 != i2:
            return -1 if i1 < i2 else 1
        return 0

    def __len__(self) -> int:
        return self._size

    @property
    def is_empty(self) -> bool:
        return self.root is None

    # ── Rotations ────────────────────────────────────────────────────────────

    def _rotate_right(self, y: AVLNode) -> AVLNode:
        x = y.left
        assert x is not None
        t2 = x.right

        x.right = y
        y.left = t2

        y.update_height()
        x.update_height()
        return x

    def _rotate_left(self, x: AVLNode) -> AVLNode:
        y = x.right
        assert y is not None
        t2 = y.left

        y.left = x
        x.right = t2

        x.update_height()
        y.update_height()
        return y

    def _rebalance(self, node: AVLNode) -> AVLNode:
        node.update_height()
        bal = node.balance

        # Left heavy
        if bal > 1:
            assert node.left is not None
            if node.left.balance < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Right heavy
        if bal < -1:
            assert node.right is not None
            if node.right.balance > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    # ── Insert ───────────────────────────────────────────────────────────────

    def insert(self, key: float, value: Any) -> None:
        """Insert (key, value) into the tree. Guaranteed O(log n)."""
        def _insert(node: Optional[AVLNode]) -> AVLNode:
            if node is None:
                self._size += 1
                return AVLNode(key=key, value=value)

            cmp = self.comparator(key, value, node.key, node.value)
            if cmp < 0:
                node.left = _insert(node.left)
            else:
                node.right = _insert(node.right)

            return self._rebalance(node)

        self.root = _insert(self.root)

    # ── Delete ───────────────────────────────────────────────────────────────

    def delete(self, key: float, value: Any) -> bool:
        """
        Delete (key, value) from the tree. Guaranteed O(log n).
        Returns True if found and deleted, False otherwise.
        """
        deleted = False

        def _min_value_node(node: AVLNode) -> AVLNode:
            curr = node
            while curr.left is not None:
                curr = curr.left
            return curr

        def _delete(node: Optional[AVLNode]) -> Optional[AVLNode]:
            nonlocal deleted
            if node is None:
                return None

            cmp = self.comparator(key, value, node.key, node.value)
            if cmp < 0:
                node.left = _delete(node.left)
            elif cmp > 0:
                node.right = _delete(node.right)
            else:
                # Found node to delete
                deleted = True
                self._size -= 1
                if node.left is None:
                    return node.right
                elif node.right is None:
                    return node.left

                # Node with two children: get inorder successor (smallest in right subtree)
                successor = _min_value_node(node.right)
                node.key = successor.key
                node.value = successor.value
                # Delete successor from right subtree
                node.right = _delete_exact(node.right, successor.key, successor.value)

            return self._rebalance(node)

        def _delete_exact(node: Optional[AVLNode], k: float, v: Any) -> Optional[AVLNode]:
            if node is None:
                return None
            cmp = self.comparator(k, v, node.key, node.value)
            if cmp < 0:
                node.left = _delete_exact(node.left, k, v)
            elif cmp > 0:
                node.right = _delete_exact(node.right, k, v)
            else:
                if node.left is None:
                    return node.right
                elif node.right is None:
                    return node.left
                succ = _min_value_node(node.right)
                node.key = succ.key
                node.value = succ.value
                node.right = _delete_exact(node.right, succ.key, succ.value)
            return self._rebalance(node)

        self.root = _delete(self.root)
        return deleted

    # ── Search & Inorder Traversal ────────────────────────────────────────────

    def inorder(self) -> list[tuple[float, Any]]:
        """Returns inorder list of (key, value) tuples in sorted order."""
        res: list[tuple[float, Any]] = []

        def _traverse(node: Optional[AVLNode]):
            if node:
                _traverse(node.left)
                res.append((node.key, node.value))
                _traverse(node.right)

        _traverse(self.root)
        return res

    def predecessor(self, key: float, value: Any) -> Optional[Any]:
        """Find the element immediately preceding (key, value) in sorted order. O(log n)."""
        pred: Optional[Any] = None
        curr = self.root
        while curr:
            cmp = self.comparator(key, value, curr.key, curr.value)
            if cmp <= 0:
                curr = curr.left
            else:
                pred = curr.value
                curr = curr.right
        return pred

    def successor(self, key: float, value: Any) -> Optional[Any]:
        """Find the element immediately succeeding (key, value) in sorted order. O(log n)."""
        succ: Optional[Any] = None
        curr = self.root
        while curr:
            cmp = self.comparator(key, value, curr.key, curr.value)
            if cmp >= 0:
                curr = curr.right
            else:
                succ = curr.value
                curr = curr.left
        return succ

    def assert_avl_invariants(self) -> None:
        """Helper for unit tests: verifies BST order and AVL height balance on every node."""
        def _check(node: Optional[AVLNode]) -> int:
            if not node:
                return 0
            lh = _check(node.left)
            rh = _check(node.right)
            assert abs(lh - rh) <= 1, f"AVL height balance violated: lh={lh}, rh={rh} at key {node.key}"
            assert node.height == 1 + max(lh, rh), "Cached height incorrect"
            if node.left:
                assert self.comparator(node.left.key, node.left.value, node.key, node.value) <= 0, "BST order violated (left)"
            if node.right:
                assert self.comparator(node.right.key, node.right.value, node.key, node.value) >= 0, "BST order violated (right)"
            return node.height

        _check(self.root)
