% 1. Define symbolic variables
syms x y t

% 2. Derivatives (Calculus)
f = x^2 + sin(x)*y;
df = diff(f, x);
disp('Derivative of x^2 + sin(x)*y:')
disp(df)

% 3. Integration
area = int(x^2, 0, 1);
disp('Integral of x^2 from 0 to 1:')
disp(area)

% 4. Expansion / Simplification
poly = (x + 1)^3;
ex = expand(poly);
disp('Expanded (x+1)^3:')
disp(ex)

% 5. Solver
sol = solve(x^2 - 4 == 0);
disp('Roots of x^2 - 4:')
disp(sol)