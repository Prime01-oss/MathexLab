clc;
clear;

[x, y] = meshgrid(-5:0.5:5);
z = x.^2 + y.^2;

surf(x, y, z)
xlabel('x')
ylabel('y')
zlabel('z')
title('3D Surface Plot')
shading interp
colorbar
