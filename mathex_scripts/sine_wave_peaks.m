% 3D Sine Peaks
x = linspace(-4*pi, 4*pi, 70);
y = linspace(-4*pi, 4*pi, 70);
[X, Y] = meshgrid(x, y);

Z = sin(X).*cos(Y);

surf(X, Y, Z);
shading interp
xlabel('X'); ylabel('Y'); zlabel('Z');
title('Sin(X) Cos(Y) Surface');
