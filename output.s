    msg db 'Resultado: ', 0
    newline db 10, 0  ; \n para Linux
    buffer times 32 db 0
section .data

section .text
global _start


suma:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    mov [rbp-8], rdi
    mov [rbp-16], rsi
    mov rax, [rbp-8]
    push rax
    mov rax, [rbp-16]
    mov rbx, rax
    pop rax
    add rax, rbx
    add rsp, 48
    pop rbp
    ret

main:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    mov dword [rbp-8], 1
    mov dword [rbp-16], 2
    mov rax, [rbp-8]
    push rax
    mov rax, [rbp-16]
    mov rbx, rax
    pop rax
    add rax, rbx
    mov dword [rbp-24], eax
    mov rax, 8
    mov rdi, rax
    mov rax, 9
    mov rsi, rax
    call suma
    mov dword [rbp-24], eax
    mov rax, [rbp-24]
    add rsp, 56
    pop rbp
    ret

print_number:
    push rbp
    mov rbp, rsp
    sub rsp, 32    ; shadow space
    push rbx
    push rcx
    push rdx
    mov rax, rdi
    mov rbx, 10
    mov rcx, buffer
    add rcx, 31     ; apuntar al final del buffer
    mov byte [rcx], 0   ; null terminator
    dec rcx
    test rax, rax
    jnz convert_loop
    mov byte [rcx], '0'
    jmp print_digits
convert_loop:
    test rax, rax
    jz print_digits
    xor rdx, rdx
    div rbx
    add dl, '0'
    mov [rcx], dl
    dec rcx
    jmp convert_loop
print_digits:
    inc rcx
    mov rdx, buffer
    add rdx, 31
    sub rdx, rcx
    push rcx        ; guardar buffer
    push rdx        ; guardar longitud
    mov rax, 1      ; sys_write
    mov rdi, 1      ; stdout
    pop rdx         ; longitud
    pop rsi         ; buffer
    syscall
    pop rdx
    pop rcx
    pop rbx
    add rsp, 32
    pop rbp
    ret
_start:
    call main
    mov rdi, rax    ; usar valor de retorno como exit code
    ; Mostrar mensaje 'Resultado: '
    push rdi        ; guardar exit code
    mov rax, 1      ; sys_write
    mov rdi, 1      ; stdout
    mov rsi, msg    ; buffer
    mov rdx, 11     ; longitud
    syscall
    pop rdi         ; recuperar el valor
    call print_number
    mov rax, 1      ; sys_write
    mov rdi, 1      ; stdout
    mov rsi, newline ; buffer
    mov rdx, 1      ; longitud
    syscall
    mov rdi, 8      ; exit code fijo para prueba
    mov rax, 60     ; sys_exit
    syscall