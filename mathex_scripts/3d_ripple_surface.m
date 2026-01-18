% 3D Ripple Plot
x = linspace(-10, 10, 50);
y = linspace(-10, 10, 50);
[X, Y] = meshgrid(x, y);

R = sqrt(X.^2 + Y.^2) + 0.01;
Z = cos(R) ./ R;

surf(X, Y, Z);
shading interp
xlabel('X'); ylabel('Y'); zlabel('Z');
title('3D Ripple Surface');
