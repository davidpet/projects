; Warning: First, seting the package where the functions will be defined 
(in-package :dp)


; Walks a tree in DFS order and computes a value on each leaf, returning a flat list of pairs of paths and values.
; The paths can be used to determine the location of each computed value in the original tree structure.
; You can leave the fn nil to just get the leaf values themselves back.
; ex: (walk-tree '(1 2 (3 4)) (lambda (val path) (print val) (print path)))
; to extract just the values, use (mapcar #'second result)
(om::defmethod! walk-tree ((tree list) fn)
  :initvals '(nil nil)
  :indoc '("a tree structure within a list" "a function that takes a leaf value and a path (list of indices) [default = just returns value back]")
  :icon 254
  :doc "walks <tree> in DFS order and calls <fn> on each leaf, returning a list of pairs of (path, value)"
  :outdoc '("list of pairs (path, fn result)")
  :numouts 1
  (labels ((recur (subtree path) 
              (if (consp subtree)
                  (append (loop for i from 0 to (1- (length subtree)) collect
                            (let ((subpath (append path (list i)))
                                  (a (nth i subtree)))
                               (recur a subpath))))
                  (list path
                        (funcall (if fn fn (lambda (x y) x)) subtree path)))))
    (recur tree nil)))

; Groups a list by the return value of a given function and returns result as a hash table.
; ex: (group-by #'first '((1 2 3) (4 5 6) (1 1 2))) -> hash table with keys 1 and 4 where 1 will have 2 lists and 4 will have 1 list
(om:defmethod! group-by (fn (list list))
  :initvals '(nil nil)
  :indoc '("fn that takes an element and returns the value to group by" "list of items to be grouped")
  :icon 254
  :doc "Builds a hash-table with the fn result as keys"
  (let ((ret (make-hash-table)))
     (loop for el in list do
       (let ((key (funcall fn el)))
          (let ((vals (gethash key ret)))
             (setf (gethash key ret) (append vals (list el))))))
     ret))
     
; Makes a tree of nil leaves out of a list of paths as returned by walk-tree.
;
; This currently only works as expected if you have all indices present at all levels and has not been tested for nil.
(om:defmethod! make-tree ((paths list))
  :initvals '(nil)
  :indoc '("List of paths (list of indices)")
  :icon 254
  :doc "Builds a tree of null values based on the structure of input path list"
  (let ((groupings (group-by #'first paths))) 
    (loop for index being the hash-keys of groupings collect  
        (let ((subpaths (mapcar #'cdr (gethash index groupings)))) 
           (if (> (length subpaths) 1)
               (make-tree subpaths)
               nil)))))
        
; Changes a value of a tree in-place by following a path recursively down.
; Returns the modified tree (which is the original tree with destructive modifications).
(om:defmethod! edit-tree ((tree list) (path list) value)
  :initvals '(nil nil nil)
  :indoc '("the tree" "list of indices" "leaf value")
  :icon 254
  :doc "Edit tree in-place to populate it with values"
  (if (> (length path) 1)
      (let ((subtree (nth (first path) tree))
            (subpath (rest path)))
         (edit-tree subtree subpath value))
      (let ((index (first path)))
         (setf (elt tree index) value)))
  tree)

; TODO: get this working
(om:defmethod! build-tree ((spec list))
  :initvals '(nil)
  :indoc '("list of pairs of path (list of indices) to leaf values")
  :icon 254
  :doc "builds a new tree based on paths and values in the spec"
  (let ((paths (mapcar #'first spec))
        (vals (mapcar #'second spec)))
     (let ((tree (make-tree paths)))
       (print paths)
       (print vals)
       (print tree)
       (mapc (lambda (p v) (edit-tree tree p v)) paths vals)
       tree)))

