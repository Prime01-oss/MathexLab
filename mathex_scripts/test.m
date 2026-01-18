% verify_physics.m
% Test Suite for MathexLab Physics Module (Step 3)

clc;
disp('========================================');
disp('   MathexLab Physics Verification     ');
disp('========================================');

failures = 0;

% ---------------------------------------------------------
% 1. Test 'physconst' Lookup
% ---------------------------------------------------------
disp('[Test 1] Core Constants Lookup');
try
    c_val = physconst('LightSpeed');
    % Check against exact speed of light
    if abs(c_val - 299792458) < 1e-5
        disp('  [PASS] LightSpeed matches exact value.');
    else
        disp('  [FAIL] LightSpeed mismatch.');
        failures = failures + 1;
    end
    
    % Test deep lookup (CODATA via SciPy)
    p_mass = physconst('proton mass');
    if p_mass > 1.67e-27 && p_mass < 1.68e-27
        disp('  [PASS] CODATA lookup (proton mass) successful.');
    else
        disp('  [FAIL] CODATA lookup failed.');
        failures = failures + 1;
    end
catch
    disp('  [CRITICAL FAIL] physconst() threw an error.');
    failures = failures + 1;
end

% ---------------------------------------------------------
% 2. Test Global Shortcuts & Structs
% ---------------------------------------------------------
disp(' ');
disp('[Test 2] Global Shortcuts');

if exist('c', 'var') && c == 299792458
    disp('  [PASS] Global variable "c" exists.');
else
    disp('  [FAIL] Global "c" missing or incorrect.');
    failures = failures + 1;
end

% hbar should be h / (2*pi)
if exist('hbar', 'var') && hbar < h
    disp('  [PASS] Global "hbar" exists and is < h.');
else
    disp('  [FAIL] Global "hbar" logic check failed.');
    failures = failures + 1;
end

% Check Struct Access (PhysicalConstants.k)
if PhysicalConstants.k > 1.38e-23 && PhysicalConstants.k < 1.39e-23
    disp('  [PASS] PhysicalConstants.k struct access works.');
else
    disp('  [FAIL] PhysicalConstants struct failed.');
    failures = failures + 1;
end

% ---------------------------------------------------------
% 3. Test Unit Converters
% ---------------------------------------------------------
disp(' ');
disp('[Test 3] Unit Converters');

% Temperature: 0 C -> 32 F
t_f = convtemp(0, 'C', 'F');
if abs(t_f - 32) < 0.01
    disp('  [PASS] convtemp(0, C, F) -> 32');
else
    disp('  [FAIL] convtemp failed.');
    failures = failures + 1;
end

% Length: 1 inch -> 2.54 cm
len_cm = convlength(1, 'in', 'cm');
if abs(len_cm - 2.54) < 0.001
    disp('  [PASS] convlength(1, in, cm) -> 2.54');
else
    disp('  [FAIL] convlength failed.');
    failures = failures + 1;
end

% Mass: 1 kg -> ~2.20462 lb
m_lb = convmass(1, 'kg', 'lb');
if abs(m_lb - 2.20462) < 0.001
    disp('  [PASS] convmass(1, kg, lb) -> ~2.205');
else
    disp('  [FAIL] convmass failed.');
    failures = failures + 1;
end

% Force: 1 kN -> 1000 N
f_n = convforce(1, 'kN', 'N');
if f_n == 1000
    disp('  [PASS] convforce(1, kN, N) -> 1000');
else
    disp('  [FAIL] convforce failed.');
    failures = failures + 1;
end

% Pressure: 1 atm -> 101325 Pa
p_pa = convpres(1, 'atm', 'Pa');
if abs(p_pa - 101325) < 1
    disp('  [PASS] convpres(1, atm, Pa) -> 101325');
else
    disp('  [FAIL] convpres failed.');
    failures = failures + 1;
end

% Energy: 1 eV -> Joules
e_j = convenergy(1, 'eV', 'J');
if abs(e_j - 1.60218e-19) < 1e-23
    disp('  [PASS] convenergy(1, eV, J) -> 1.602e-19');
else
    disp('  [FAIL] convenergy failed.');
    failures = failures + 1;
end

% ---------------------------------------------------------
% Summary
% ---------------------------------------------------------
disp(' ');
disp('========================================');
if failures == 0
    disp('SUCCESS: All Systems Operational.');
    disp('You are ready for physics simulations!');
else
    disp(['WARNING: ' num2str(failures) ' tests failed.']);
end
disp('========================================');