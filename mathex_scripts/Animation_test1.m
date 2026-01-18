% Create the animated line
h = animatedline();

% Set up data
x = linspace(0, 4*pi, 1000);

% Loop using MATLAB syntax (1:length instead of range)
for k = 1:length(x)
    % Use () for indexing, not []
    addpoints(h, x(k), sin(x(k)));
    
    % Update the plot
    drawnow; 
end