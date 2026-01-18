% Simple MATLAB Script
% Task: Square numbers from 1 to 10 and plot them

clc;
clear;
close all;
clf;

% Create a vector
x = 1:10;

% Preallocate for efficiency
y = zeros(size(x));

% Compute squares using a loop
for i = 1:length(x)
    y(i) = x(i)^2;
end

% Display results
disp('Numbers and their squares:')
disp([x' y'])

% Plot the result
figure;
plot(x, y, 'o-', 'LineWidth', 2);
xlabel('Number');
ylabel('Square');
title('Square of Numbers from 1 to 10');
grid on;
