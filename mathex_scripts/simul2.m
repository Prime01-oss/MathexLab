clear all; clf;
% Optimization and Calculus Test

disp('--- Optimization Test ---')

% 1. Find Minimum of Rosenbrock Function (Banana Function)
% f(x,y) = (1-x)^2 + 100*(y-x^2)^2
fun = @(v) (1 - v(1))^2 + 100 * (v(2) - v(1)^2)^2;
x0 = [-1.2, 1];

disp('Minimizing Rosenbrock function...')
x_min = fminsearch(fun, x0);
disp('Minimum found at:')
disp(x_min)
disp('Expected: [1 1]')

% 2. Polynomials
p = [1 -5 6]; % x^2 - 5x + 6 (Roots: 2, 3)
r = roots(p);
disp('Roots of x^2 - 5x + 6:')
disp(r)

% Evaluate polynomial at x=0:0.5:4
x_val = 0:0.5:4;
y_val = polyval(p, x_val);

% 3. Numerical Integration
area = trapz(y_val, x_val);
disp('Area under curve (Trapz):')
disp(area)

% 4. Plot Result
figure
plot(x_val, y_val, 'o-')
hold on
plot(r, [0 0], 'rx', 'MarkerSize', 10)
title('Polynomial & Roots')
grid on