clear all; clf;
% Physics Simulation: Damped Harmonic Oscillator
% Differential Equation: y'' + 0.5*y' + 10*y = 0

disp('Running Physics Simulation...')

% 1. Define ODE Function (Anonymous)
% State vector y = [position; velocity]
dydt = @(t, y) [y(2); -0.5*y(2) - 10*y(1)];

% 2. Solve ODE
tspan = 0:0.1:20;
y0 = [1; 0];  % Initial pos=1, vel=0
sol = ode45(dydt, tspan, y0);

% 3. Extract results
t = sol.x;
pos = sol.y(1, :);

% 4. Frequency Analysis (FFT)
L = length(pos);
Y = fft(pos);
P2 = abs(Y/L);
P1 = P2(1:floor(L/2)+1);
f = (0:(L/2))/L * (1/0.1); % Approx frequency vector

% 5. Visualization
figure
subplot(2, 1, 1)
plot(t, pos, 'LineWidth', 2)
title('Damped Oscillator Position')
xlabel('Time (s)')
ylabel('Position (m)')
grid on

subplot(2, 1, 2)
plot(f, P1, 'r', 'LineWidth', 2)
title('Frequency Spectrum (FFT)')
xlabel('Frequency (Hz)')
ylabel('Magnitude')
grid on

disp('Simulation Complete.')