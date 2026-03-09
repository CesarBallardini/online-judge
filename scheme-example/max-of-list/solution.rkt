(define (max-of-list lst)
  (if (null? lst)
      (error "empty list")
      (let loop ((rest (cdr lst)) (mx (car lst)))
        (if (null? rest)
            mx
            (loop (cdr rest) (if (> (car rest) mx) (car rest) mx))))))
