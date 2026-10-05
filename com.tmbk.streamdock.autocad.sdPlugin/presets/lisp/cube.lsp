;;; Cube nomme, converti en bloc puis insere a l'origine choisie.
;;; Appel : (c:tmbk-cube)  -  les parametres sont demandes dans la ligne de commande.

(defun tmbk-ask-name (default / name)
  (setq name (getstring T (strcat "\nNom du bloc <" default ">: ")))
  (if (= name "") default name)
)

(defun tmbk-ask-size (default / size)
  (setq size (getdist (strcat "\nTaille du cube <" (rtos default 2 2) ">: ")))
  (if (null size) default size)
)

(defun tmbk-ask-origin (default / origin)
  (setq origin (getpoint "\nPoint d'insertion <0,0,0>: "))
  (if (null origin) default origin)
)

(defun tmbk-define-block (name origin entity)
  (if (tblsearch "BLOCK" name)
    (command "_.-BLOCK" name "_Y" "_non" origin entity "")
    (command "_.-BLOCK" name "_non" origin entity "")
  )
)

(defun c:tmbk-cube (/ name size origin old-osmode)
  (setq name (tmbk-ask-name "Cube"))
  (setq size (tmbk-ask-size 100.0))
  (setq origin (tmbk-ask-origin '(0.0 0.0 0.0)))
  (setq old-osmode (getvar "OSMODE"))
  (setvar "OSMODE" 0)
  (command "_.BOX" "_non" origin "_C" size)
  (tmbk-define-block name origin (entlast))
  (command "_.-INSERT" name "_non" origin 1 1 0)
  (setvar "OSMODE" old-osmode)
  (princ (strcat "\nBloc " name " cree et insere."))
  (princ)
)

(princ "\nTMBK : tapez TMBK-CUBE ou utilisez la touche Stream Dock.")
(princ)
