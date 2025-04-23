from graphviz import Digraph, Source

class BPlusTreeNode:
    def __init__(self, order, is_leaf=True):
        self.order = order                  # Maximum number of children a node can have
        self.is_leaf = is_leaf              # Flag to check if node is a leaf
        self.keys = []                      # List of keys in the node
        self.values = []                    # Used in leaf nodes to store associated values
        self.children = []                  # Used in internal nodes to store child pointers
        self.next = None                    # Points to next leaf node for range queries

    def is_full(self):
        # A node is full if it has reached the maximum number of keys (order - 1)
        return len(self.keys) >= self.order - 1


class BPlusTree:
    def __init__(self, order=8):
        self.order = order
        self.root = BPlusTreeNode(order=order)

    def search(self, key):
        current = self.root
        while not current.is_leaf:
            i = 0
            while i < len(current.keys) and key >= current.keys[i]:
                i += 1
            current = current.children[i]

        # Now at a leaf node
        for i, k in enumerate(current.keys):
            if k == key:
                return current.values[i]
        return None


    def insert(self, key, value):
        root = self.root
        if len(root.keys) == self.order - 1:
            new_root = BPlusTreeNode(order=self.order, is_leaf=False)

            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node, key, value):
        if node.is_leaf:
            # Insert in sorted order
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            node.keys.insert(i, key)
            node.values.insert(i, value)
        else:
            # Find child to recurse into
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            child = node.children[i]
            if len(child.keys) == self.order - 1:
                self._split_child(node, i)
                # After split, decide which child to go down
                if key >= node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent, index):
        child = parent.children[index]
        mid = len(child.keys) // 2

        if child.is_leaf:
            # Split leaf
            new_leaf = BPlusTreeNode(order=self.order, is_leaf=True)
            new_leaf.keys = child.keys[mid:]
            new_leaf.values = child.values[mid:]
            child.keys = child.keys[:mid]
            child.values = child.values[:mid]

            # Maintain linked list
            new_leaf.next = child.next
            child.next = new_leaf

            # Promote first key of new leaf
            parent.keys.insert(index, new_leaf.keys[0])
            parent.children.insert(index + 1, new_leaf)
        else:
            # Split internal node
            new_internal = BPlusTreeNode(order=self.order, is_leaf=False)
            # Promote the middle key
            promote_key = child.keys[mid]
            new_internal.keys = child.keys[mid+1:]
            new_internal.children = child.children[mid+1:]

            # Update left child
            child.keys = child.keys[:mid]
            child.children = child.children[:mid+1]

            parent.keys.insert(index, promote_key)
            parent.children.insert(index + 1, new_internal)


    def delete(self, key):
        success = self._delete(self.root, key)

        # Shrink root if needed
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

        return success
    
    def _delete(self, node, key):
        if node.is_leaf:
            if key in node.keys:
                i = node.keys.index(key)
                node.keys.pop(i)
                node.values.pop(i)
                return True
            return False

        # internal node
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1

        child = node.children[i]
        result = self._delete(child, key)

        # If child underflows
        min_keys = (self.order // 2) 
        if len(child.keys) < min_keys:
            self._fill_child(node, i)

        return result
    
    def _fill_child(self, node, index):
        if index > 0 and len(node.children[index - 1].keys) > (self.order // 2) - 1:
            self._borrow_from_prev(node, index)
        elif index < len(node.children) - 1 and len(node.children[index + 1].keys) > (self.order // 2) - 1:
            self._borrow_from_next(node, index)
        else:
            # Merge with sibling
            if index < len(node.children) - 1:
                self._merge(node, index)
            else:
                self._merge(node, index - 1)

    def _borrow_from_prev(self, node, index):
        child = node.children[index]
        left_sibling = node.children[index - 1]

        if child.is_leaf:
            # borrow key-value from left sibling
            child.keys.insert(0, left_sibling.keys.pop(-1))
            child.values.insert(0, left_sibling.values.pop(-1))
            node.keys[index - 1] = child.keys[0]
        else:
            # borrow key + pointer
            child.keys.insert(0, node.keys[index - 1])
            child.children.insert(0, left_sibling.children.pop(-1))
            node.keys[index - 1] = left_sibling.keys.pop(-1)

    def _borrow_from_next(self, node, index):
        child = node.children[index]
        right_sibling = node.children[index + 1]

        if child.is_leaf:
            child.keys.append(right_sibling.keys.pop(0))
            child.values.append(right_sibling.values.pop(0))
            node.keys[index] = right_sibling.keys[0]
        else:
            child.keys.append(node.keys[index])
            child.children.append(right_sibling.children.pop(0))
            node.keys[index] = right_sibling.keys.pop(0)

    def _merge(self, node, index):
        child = node.children[index]
        sibling = node.children[index + 1]

        if child.is_leaf:
            child.keys.extend(sibling.keys)
            child.values.extend(sibling.values)
            child.next = sibling.next
        else:
            child.keys.append(node.keys[index])
            child.keys.extend(sibling.keys)
            child.children.extend(sibling.children)

        node.keys.pop(index)
        node.children.pop(index + 1)

    def update(self, key, new_value):
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]

        # now node is a leaf
        if key in node.keys:
            index = node.keys.index(key)
            node.values[index] = new_value
            return True
        return False

    def range_query(self, start_key, end_key):
        result = []
        node = self.root

        # navigate to starting leaf
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and start_key >= node.keys[i]:
                i += 1
            node = node.children[i]

        # collect keys in range
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
            node = node.children[0]

        while node:
            for k, v in zip(node.keys, node.values):
                result.append((k, v))
            node = node.next

        return result
    
    def visualize_tree(self):
        """
        Generates a Graphviz Digraph object for visualization.
        Uses HTML-like labels with single-row internal nodes and detailed leaf nodes.
        """

        # Use node_attr shape='plain' so HTML table defines the shape
        dot = Digraph(comment='B+ Tree', node_attr={'shape': 'plain'})

        if not self.root or (self.root.is_leaf and not self.root.keys):
            dot.node('empty', 'Tree is empty'); return dot

        node_queue = [(self.root, 'node_root')]
        node_id_map = {self.root: 'node_root'}
        id_counter = 0
        processed_nodes = set()
        all_leaf_render_info = []

        while node_queue:
            current_node, node_id = node_queue.pop(0)
            if current_node in processed_nodes: continue
            processed_nodes.add(current_node)

            # --- HTML Label Generation ---
            # Use border=1 for debugging, 0 for final look
            html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'

            # <<< CORRECTED Internal Node HTML (Single Row: P0 | K1 | P1 | K2 | P2 ...) >>>
            if not current_node.is_leaf:
                html_label += '<TR>'
                html_label += f'<TD PORT="f0">P0</TD>' # First pointer port
                for i, key in enumerate(current_node.keys):
                    html_label += f'<TD>{key}</TD>' # Key cell
                    html_label += f'<TD PORT="f{i+1}">P{i+1}</TD>' # Next pointer port
                html_label += '</TR>'
                html_label += '</TABLE>>'
                dot.node(node_id, label=html_label) # Node uses the HTML label

                # Add children & edges (Connect TO pointer ports f{i})
                for i, child in enumerate(current_node.values):
                    if child not in node_id_map:
                         id_counter += 1; child_id = f"node_{id_counter}"; node_id_map[child] = child_id
                    else: child_id = node_id_map[child]
                    if child not in processed_nodes and child not in [n for n, id_str in node_queue]: node_queue.append((child, child_id))
                    # Ensure edge targets the correct port name defined above
                    dot.edge(f"{node_id}:f{i}", child_id)
            # <<< END CORRECTED Internal Node HTML >>>

            else: # Leaf Node (Detailed View from previous step)
                if not current_node.keys:
                    html_label += '<TR><TD BGCOLOR="lightblue">Empty Leaf</TD></TR>'
                else:
                    # Create one cell per Key-Value pair in the leaf
                    label_content = '<TR>'
                    for i, key in enumerate(current_node.keys):
                        value = current_node.values[i]
                        # Create a compact representation of the record
                        record_repr = f"Key: {key}<BR/>"
                        if isinstance(value, dict):
                            count = 0; max_fields_to_show = 2
                            for rec_key, rec_val in value.items():
                                if rec_key == key: continue # Skip main key
                                val_str = str(rec_val); val_str = (val_str[:8] + '...') if len(val_str) > 10 else val_str
                                record_repr += f"{rec_key}: {val_str}<BR/>"
                                count += 1
                                if count >= max_fields_to_show: break
                        else: record_repr += f"Value: {str(value)[:15]}"
                        # Add cell for this key-record pair
                        label_content += f'<TD PORT="kv{i}" BGCOLOR="lightblue" ALIGN="LEFT">{record_repr}</TD>'
                    label_content += '</TR>'
                    html_label += label_content
                html_label += '</TABLE>>'
                dot.node(node_id, label=html_label)
                all_leaf_render_info.append((current_node, node_id))
            # --- End Label Generation ---

        # --- Draw Leaf Links ---
        # (Leaf linking logic remains the same)
        first_leaf = self.root
        while first_leaf and not first_leaf.is_leaf:
             if not first_leaf.values: break
             first_leaf = first_leaf.values[0] # type: ignore
        obj_to_id = {node_obj: node_str_id for node_obj, node_str_id in all_leaf_render_info}; visited_leaves = set(); current_leaf_obj = first_leaf
        while current_leaf_obj and current_leaf_obj not in visited_leaves:
            visited_leaves.add(current_leaf_obj); current_leaf_id = obj_to_id.get(current_leaf_obj); next_leaf_obj = current_leaf_obj.next; next_leaf_id = obj_to_id.get(next_leaf_obj)
            if current_leaf_id and next_leaf_id: dot.edge(f"{current_leaf_id}", f"{next_leaf_id}", style='dashed', arrowhead='none', constraint='false')
            current_leaf_obj = next_leaf_obj
        # --- End Leaf Links ---

        # Save as SVG
        dot.format = 'svg'
        dot.render('output_graph', cleanup=True)  # Produces output_graph.svg
        return dot


