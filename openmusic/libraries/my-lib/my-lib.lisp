;--<ma-lib> is just an example for pedagogical purposes ( Malt, ircam 2006)
;-----------------------------------------------
;-----------------------------------------------
;Package Definition (Optional but very useful, 
;it help to avoid mismatch between your function names and with OM function names, 
;If no package was defined,  package :OM will be used.
; It's a good practice, always, defining your own packages!!!!
;--------------------------------------------------

(defpackage :dp) ; <mfl> is just a symbol, it means : "my function library" (you also could use <john>) 

(in-package :dp)

;--------------------------------------------------
;Loading files 
;--------------------------------------------------

(mapc 'om::compile&load 
      (list
       (make-pathname  :directory (append (pathname-directory *load-pathname*) (list "sources")) :name "trees" :type "lisp")
       ))

; using "make-pathname" and *load-pathname*, allow us to put our library anywhere

;--------------------------------------------------
; Seting the menu and sub-menu structure, and filling packages
; The sub-list syntax:
; ("sub-pack-name" subpack-lists class-list function-list class-alias-list)
;--------------------------------------------------

(om::fill-library 
 '(("trees" Nil Nil (walk-tree group-by make-tree ) Nil)
   ))


