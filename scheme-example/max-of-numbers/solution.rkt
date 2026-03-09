#lang racket
(define n (read))
(if (= n 0)
    (displayln "EMPTY")
    (let loop ([i 1] [mx (read)])
      (if (= i n)
          (displayln mx)
          (loop (+ i 1) (max mx (read))))))
