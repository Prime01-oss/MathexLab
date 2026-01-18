% ==============================================================================
% MATHEXLAB STRESS TEST SUITE
% ==============================================================================
disp('Starting System Stress Test...');
tic;

% ------------------------------------------------------------------------------
% PHASE 1: HEAVY LINEAR ALGEBRA (Tests NumPy/LAPACK linkage)
% ------------------------------------------------------------------------------
disp('Phase 1: Generating 2000x2000 random matrix...');
N = 2000;
A = rand(N);

disp('Phase 1: Inverting matrix (O(N^3) operation)...');
B = inv(A);

disp('Phase 1: Computing Eigenvalues for 1000x1000 matrix...');
C = eig(A(1:1000, 1:1000));

t1 = toc;
disp(['Phase 1 Complete. Time: ' num2str(t1) 's']);

% ------------------------------------------------------------------------------
% PHASE 2: INTERPRETER LOOP STRESS (Tests Parser & Transpiler Speed)
% Generating the Mandelbrot Set pixel-by-pixel
% ------------------------------------------------------------------------------
disp('Phase 2: Mandelbrot Fractal (Scalar Loops)...');

grid_size = 100; % 100x100 = 10,000 iterations of nested loops
max_iter = 50;
x = linspace(-2, 1, grid_size);
y = linspace(-1.5, 1.5, grid_size);
Z = zeros(grid_size, grid_size);

% Nested loops are the weakness of interpreted languages.
% This checks if your transpiler adds too much overhead.
for i = 1:grid_size
    for j = 1:grid_size
        c = x(i) + 1i * y(j);
        z = 0;
        iter = 0;
        
        while abs(z) < 2 && iter < max_iter
            z = z^2 + c;
            iter = iter + 1;
        end
        Z(j, i) = iter;
    end
end

t2 = toc;
disp(['Phase 2 Complete. Cumulative Time: ' num2str(t2) 's']);

% ------------------------------------------------------------------------------
% PHASE 3: SOLVER STRESS (Tests the new pdepe optimization)
% ------------------------------------------------------------------------------
disp('Phase 3: High-Resolution Heat Equation...');

m = 0;
x_mesh = linspace(0, 1, 500); % Dense mesh
t_span = linspace(0, 1, 20);

% Define physics inline
pdefun = @(x,t,u,dudx) deal(1, dudx, 0); % Heat equation
icfun  = @(x) sin(pi*x);
bcfun  = @(xl,ul,xr,ur,t) deal(0, ul, 0, ur);

sol = pdepe(m, pdefun, icfun, bcfun, x_mesh, t_span);

t3 = toc;
disp(['Phase 3 Complete. Cumulative Time: ' num2str(t3) 's']);

% ------------------------------------------------------------------------------
% PHASE 4: VISUALIZATION
% ------------------------------------------------------------------------------
disp('Phase 4: Rendering Plots...');

figure;
subplot(2, 2, 1);
imagesc(A);
title('Random Matrix Heatmap');

subplot(2, 2, 2);
contourf(x, y, Z);
title('Mandelbrot Fractal');
colorbar;

subplot(2, 2, [3, 4]);
surf(sol);
title('PDE Solution Surface');
shading('interp');

disp('DONE. System survived.');