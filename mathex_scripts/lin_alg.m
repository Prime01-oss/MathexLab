% Linear Algebra Verification

clc
disp('--- Linear Algebra Test ---')

% 1. Dense Matrix Eigenvalues
A = [1 2 3; 2 5 1; 3 1 6];
disp('Matrix A:')
disp(A)

[V, D] = eig(A);
disp('Eigenvalues (Diagonal D):')
disp(D)

% 2. Matrix Exponential (Quantum Mechanics)
% Pauli X Matrix
SigX = [0 1; 1 0];
U = expm(1i * pi * SigX);
disp('Evolution Operator U = expm(i*pi*SigX) [Expected ~ -I]:')
disp(U)

% 3. Singular Value Decomposition
[U, S, V] = svd(A);
disp('Singular Values (S):')
disp(S)

% 4. Inverse and Condition Number
A_inv = inv(A);
k = cond(A);
disp('Condition Number:')
disp(k)
disp('Check Identity (A * inv(A)):')
disp(A * A_inv)

% 5. Sparse Matrix Test
disp('Testing Sparse Matrix...')
N = 100;
S = sparse(1:N, 1:N, 1:N); % Diagonal 1..100
[Vs, Ds] = eig(S, 2, 0);    % Find 2 smallest eigenvalues near 0
disp('Smallest Sparse Eigenvalues:')
disp(Ds)