% Hyperbolic Saddle (z = x^2 - y^2)
clear; clf;

% Define grid
[x, y] = meshgrid(-3:0.1:3);

% Saddle equation
z = x.^2 - y.^2;

% Plot
surf(x, y, z);
shading interp
colormap turbo
axis equal
title('Hyperbolic Saddle Surface');
xlabel('X'); ylabel('Y'); zlabel('Z');
view(40, 25);
grid on
