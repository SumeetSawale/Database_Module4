
import math 
from graphviz import Digraph
import html 

class BPlusTreeNode:
    def __init__(self, order, is_leaf=True):
        self.order = order
        self.is_leaf = is_leaf
        self.keys = []
        self.values = []  
        self.children = [] 
        self.next = None     

    def is_full(self):
        return len(self.keys) >= self.order - 1

    def min_keys(self):
        if self.is_leaf:
            return math.floor(self.order / 2)
        else:
            return math.ceil(self.order / 2) - 1

    def is_underflow(self, is_root):
        return not is_root and len(self.keys) < self.min_keys()

class BPlusTree:
    def __init__(self, order=8):
        if order < 3:
            raise ValueError("Order must be at least 3")
        self.order = order
        self.root = BPlusTreeNode(order=order, is_leaf=True) 

    def _find_leaf(self, key):
        current = self.root
        while not current.is_leaf:
            i = 0
            while i < len(current.keys) and key >= current.keys[i]:
                i += 1
            if i < len(current.children):
                 current = current.children[i]
            elif current.children: # Should only happen if key >= last key
                 current = current.children[-1]
            else:
                 break
        return current

    def search(self, key):
        leaf_node = self._find_leaf(key)
        try:
            index = leaf_node.keys.index(key)
            return leaf_node.values[index]
        except ValueError:
            return None

    def insert(self, key, value):
        # (Keep insert, _insert_non_full, _split_child as previously corrected)
        root = self.root
        if root.is_full():
            new_root = BPlusTreeNode(order=self.order, is_leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node, key, value):
        if node.is_leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            node.keys.insert(i, key)
            node.values.insert(i, value)
        else:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            child = node.children[i]
            if child.is_full():
                self._split_child(node, i)
                if key >= node.keys[i]: # Check if key should go into the newly split node
                    i += 1
            self._insert_non_full(node.children[i], key, value)


    def _split_child(self, parent, index):
        child_to_split = parent.children[index]
        # Use floor(m/2) keys for leaf split point index
        leaf_split_index = math.floor(self.order / 2)
        # Use ceil(m/2)-1 key index for internal split promotion
        internal_promote_key_index = math.ceil(self.order / 2) - 1

        new_node = BPlusTreeNode(order=self.order, is_leaf=child_to_split.is_leaf)

        if child_to_split.is_leaf:
             # Leaf split
             new_node.keys = child_to_split.keys[leaf_split_index:]
             new_node.values = child_to_split.values[leaf_split_index:]
             child_to_split.keys = child_to_split.keys[:leaf_split_index]
             child_to_split.values = child_to_split.values[:leaf_split_index]

             new_node.next = child_to_split.next
             child_to_split.next = new_node
             # Promote first key of new leaf
             parent.keys.insert(index, new_node.keys[0])
             parent.children.insert(index + 1, new_node)
        else:
             # Internal node split
             promote_key = child_to_split.keys[internal_promote_key_index]
             # Keys *after* promoted key go to new node
             new_node.keys = child_to_split.keys[internal_promote_key_index + 1:]
             # Children corresponding to keys *after* promoted key go to new node
             new_node.children = child_to_split.children[internal_promote_key_index + 1:]

             child_to_split.keys = child_to_split.keys[:internal_promote_key_index]
             child_to_split.children = child_to_split.children[:internal_promote_key_index + 1]

             parent.keys.insert(index, promote_key)
             parent.children.insert(index + 1, new_node)



    def delete(self, key):
        if not self.root or (self.root.is_leaf and not self.root.keys):
            print(f"Deletion failed: Key {key} not found in empty tree.")
            return False # Key not found

        deleted = self._delete(self.root, key)

        if not deleted:
             print(f"Deletion failed: Key {key} not found.")
             return False

        # Shrink root if necessary
        if not self.root.is_leaf and len(self.root.keys) == 0 and self.root.children:
            self.root = self.root.children[0]
        elif self.root.is_leaf and not self.root.keys:
             # If root is leaf and now empty, tree is empty (handled by check at start)
             pass # Or re-init root? self.root = BPlusTreeNode(order=self.order, is_leaf=True)

        print(f"Deletion successful: Key {key} removed.")
        return True


    def _delete(self, node, key):
        is_root = (node == self.root)

        if node.is_leaf:
            try:
                idx = node.keys.index(key)
                node.keys.pop(idx)
                node.values.pop(idx)
                return True # Found and deleted in leaf
            except ValueError:
                return False # Key not in this leaf
        else:
            # --- Internal Node ---
            # Find the child subtree that might contain the key
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            child = node.children[i]

            # Recursively delete from the child subtree
            deleted_in_child = self._delete(child, key)

            # If deletion occurred in the child, check if child is now underflowing
            if deleted_in_child:
                if child.is_underflow(is_root=(child == self.root)): # Pass is_root for child
                    self._rebalance_child(node, i) # Rebalance the parent's children list at index i

            return deleted_in_child # Propagate success/failure up


    def _rebalance_child(self, parent, child_index):
        """Handles underflow in parent.children[child_index] by borrowing or merging."""
        child = parent.children[child_index]
        min_keys = child.min_keys() # Get min keys for this node type

        # Try borrowing from left sibling
        if child_index > 0:
            left_sibling = parent.children[child_index - 1]
            if len(left_sibling.keys) > min_keys:
                self._borrow_from_prev(parent, child_index)
                return # Borrowing successful

        # Try borrowing from right sibling
        if child_index < len(parent.children) - 1:
            right_sibling = parent.children[child_index + 1]
            if len(right_sibling.keys) > min_keys:
                self._borrow_from_next(parent, child_index)
                return # Borrowing successful

        # If borrowing failed, merge
        if child_index < len(parent.children) - 1:
            # Merge with right sibling
            self._merge(parent, child_index)
        else:
            # Merge with left sibling (adjust index)
            self._merge(parent, child_index - 1)


    def _borrow_from_prev(self, parent, child_index):
        """Borrows a key from the left sibling."""
        child = parent.children[child_index]
        left_sibling = parent.children[child_index - 1]
        parent_key_index = child_index - 1

        if child.is_leaf:
            # Move last key/value from left sibling to start of child
            borrowed_key = left_sibling.keys.pop(-1)
            borrowed_value = left_sibling.values.pop(-1)
            child.keys.insert(0, borrowed_key)
            child.values.insert(0, borrowed_value)
            # Update parent key to reflect the new smallest key in the right child (which is 'child')
            parent.keys[parent_key_index] = child.keys[0]
        else: # Internal node
            # Move parent key down to start of child keys
            parent_key = parent.keys[parent_key_index]
            child.keys.insert(0, parent_key)
            # Move last key from left sibling up to parent
            parent.keys[parent_key_index] = left_sibling.keys.pop(-1)
            # Move last child pointer from left sibling to start of child children
            borrowed_child = left_sibling.children.pop(-1)
            child.children.insert(0, borrowed_child)


    def _borrow_from_next(self, parent, child_index):
        """Borrows a key from the right sibling."""
        child = parent.children[child_index]
        right_sibling = parent.children[child_index + 1]
        parent_key_index = child_index

        if child.is_leaf:
            # Move first key/value from right sibling to end of child
            borrowed_key = right_sibling.keys.pop(0)
            borrowed_value = right_sibling.values.pop(0)
            child.keys.append(borrowed_key)
            child.values.append(borrowed_value)
            # Update parent key to reflect the new smallest key in the right sibling
            parent.keys[parent_key_index] = right_sibling.keys[0]
        else: # Internal node
            # Move parent key down to end of child keys
            parent_key = parent.keys[parent_key_index]
            child.keys.append(parent_key)
            # Move first key from right sibling up to parent
            parent.keys[parent_key_index] = right_sibling.keys.pop(0)
            # Move first child pointer from right sibling to end of child children
            borrowed_child = right_sibling.children.pop(0)
            child.children.append(borrowed_child)


    def _merge(self, parent, merge_child_index):
        left_child = parent.children[merge_child_index]
        right_sibling = parent.children[merge_child_index + 1]
        parent_key_index = merge_child_index

        # Key to pull down from parent
        parent_key = parent.keys.pop(parent_key_index)

        if left_child.is_leaf:
            # Append keys and values from right sibling to left child
            left_child.keys.extend(right_sibling.keys)
            left_child.values.extend(right_sibling.values)
            # Update linked list pointer
            left_child.next = right_sibling.next
        else: # Internal node
            # Append parent key and right sibling keys to left child keys
            left_child.keys.append(parent_key)
            left_child.keys.extend(right_sibling.keys)
            # Append right sibling children to left child children
            left_child.children.extend(right_sibling.children)

        # Remove right sibling pointer from parent
        parent.children.pop(merge_child_index + 1)
        # (Python's garbage collector will handle the right_sibling object)


    def update(self, key, new_value):
        leaf_node = self._find_leaf(key)
        try:
            index = leaf_node.keys.index(key)
            leaf_node.values[index] = new_value
            return True
        except ValueError:
            return False

    def range_query(self, start_key, end_key):
        result = []
        node = self._find_leaf(start_key)
        while node:
            for i, key in enumerate(node.keys):
                if start_key <= key <= end_key:
                    result.append((key, node.values[i]))
                elif key > end_key:
                    return result
            node = node.next
        return result

    def get_all(self):
        result = []
        node = self.root
        while not node.is_leaf:
            if not node.children: return []
            node = node.children[0]
        while node:
            for k, v in zip(node.keys, node.values):
                result.append((k, v))
            node = node.next
        return result


    def _generate_record_html(self, record_data):
        """Creates HTML label for a separate record node."""
        if not isinstance(record_data, dict):
            return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightyellow"><TR><TD>{html.escape(str(record_data))}</TD></TR></TABLE>>'
        html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightyellow" ALIGN="LEFT">'
        for r_key, r_value in record_data.items():
            escaped_key = html.escape(str(r_key))
            escaped_value = html.escape(str(r_value))
            html_label += f'<TR><TD ALIGN="LEFT">{escaped_key}</TD><TD ALIGN="LEFT">{escaped_value}</TD></TR>'
        html_label += '</TABLE>>'
        return html_label

    def _discover_nodes_and_edges(self):
        """Traverses tree, plans nodes (incl. separate records) and edges."""
        node_id_map = {id(self.root): 'node_root'}
        id_counter = 0
        nodes_to_draw = {}
        edges_to_draw = []
        leaf_link_nodes = {}

        discovery_queue = [self.root] if self.root and (self.root.keys or not self.root.is_leaf) else [] # Handle empty root case
        discovered_ids = {id(self.root)} if self.root else set()

        while discovery_queue:
            current_node = discovery_queue.pop(0)
            current_node_obj_id = id(current_node)
            node_id_str = node_id_map[current_node_obj_id]

            if not current_node.is_leaf:
                html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
                html_label += '<TR>'
                html_label += f'<TD PORT="p0" BGCOLOR="grey90"> </TD>'
                for i, key in enumerate(current_node.keys):
                    html_label += f'<TD>{html.escape(str(key))}</TD>'
                    html_label += f'<TD PORT="p{i+1}" BGCOLOR="grey90"> </TD>'
                html_label += '</TR>'
                html_label += '</TABLE>>'
                nodes_to_draw[node_id_str] = html_label

                for i, child in enumerate(current_node.children):
                    child_obj_id = id(child)
                    if child_obj_id not in node_id_map:
                        id_counter += 1
                        child_id_str = f"node_{id_counter}"
                        node_id_map[child_obj_id] = child_id_str
                    else:
                        child_id_str = node_id_map[child_obj_id]

                    edges_to_draw.append((f"{node_id_str}:p{i}", child_id_str))

                    if child_obj_id not in discovered_ids:
                        discovered_ids.add(child_obj_id)
                        discovery_queue.append(child)
            else: # Leaf Node
                leaf_link_nodes[current_node_obj_id] = node_id_str
                html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightblue">'
                if not current_node.keys:
                    html_label += '<TR><TD>Empty Leaf</TD></TR>' # Should ideally not happen post-merge unless root
                else:
                    html_label += '<TR>'
                    for i, key in enumerate(current_node.keys):
                        html_label += f'<TD PORT=\"k{i}\">{html.escape(str(key))}</TD>'
                        value = current_node.values[i]
                        record_node_id = f"rec_{node_id_str}_{i}"
                        record_html = self._generate_record_html(value)
                        nodes_to_draw[record_node_id] = record_html
                        edges_to_draw.append((f"{node_id_str}:k{i}", record_node_id))
                    html_label += '</TR>'
                html_label += '</TABLE>>'
                nodes_to_draw[node_id_str] = html_label

        return nodes_to_draw, edges_to_draw, leaf_link_nodes

    def _add_nodes(self, dot, nodes_to_draw):
        for node_id_str, label_html in nodes_to_draw.items():
            dot.node(node_id_str, label=label_html)

    def _add_edges(self, dot, edges_to_draw, leaf_link_nodes):
        for source_port, target_id in edges_to_draw:
            dot.edge(source_port, target_id)

        first_leaf_obj = self.root
        while first_leaf_obj and not first_leaf_obj.is_leaf:
            if not first_leaf_obj.children: break
            first_leaf_obj = first_leaf_obj.children[0]

        current_leaf_obj = first_leaf_obj
        visited_leaf_ids = set()
        while current_leaf_obj:
            current_leaf_obj_id = id(current_leaf_obj)
            if current_leaf_obj_id in visited_leaf_ids: break
            visited_leaf_ids.add(current_leaf_obj_id)

            current_leaf_id_str = leaf_link_nodes.get(current_leaf_obj_id)
            next_leaf_obj = current_leaf_obj.next
            next_leaf_id_str = leaf_link_nodes.get(id(next_leaf_obj)) if next_leaf_obj else None

            if current_leaf_id_str and next_leaf_id_str:
                dot.edge(current_leaf_id_str, next_leaf_id_str,
                         style='dashed', arrowhead='none', constraint='false')

            current_leaf_obj = next_leaf_obj

    def visualize_tree(self):
        dot = Digraph(comment='B+ Tree', node_attr={'shape': 'plain'})
        dot.graph_attr['rankdir'] = 'TB'
        dot.graph_attr['nodesep'] = '0.6' # Adjusted separation
        dot.graph_attr['ranksep'] = '0.8' # Adjusted separation

        if not self.root or (self.root.is_leaf and not self.root.keys):
            dot.node('empty', 'Tree is empty')
            return dot

        nodes_to_draw, edges_to_draw, leaf_link_nodes = self._discover_nodes_and_edges()
        self._add_nodes(dot, nodes_to_draw)
        self._add_edges(dot, edges_to_draw, leaf_link_nodes)

        return dot

