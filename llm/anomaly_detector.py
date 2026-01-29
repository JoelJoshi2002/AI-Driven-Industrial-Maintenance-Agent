"""
Autonomous Anomaly Detection Module
Detects anomalies based on physics constraints without user input.
"""
from typing import Dict, Optional, List
from datetime import datetime

class AnomalyDetector:
    """
    Autonomous anomaly detection based on sensor thresholds.
    Implements physics-based constraints for industrial machinery.
    """
    
    # Threshold definitions
    #
    # IMPORTANT ABOUT UNITS / DATASETS
    # - Our API exposes `temperature` as Kelvin (from `process_temp_k` in the DB).
    # - The "Thermal Runaway < 190°C while printing" rule is a 3D-printer hotend concept.
    #   It should NOT trigger for "ambient-ish" process temperatures around 300–315K.
    #
    # We therefore gate Thermal Runaway behind an approximate "printing temperature"
    # threshold to avoid false positives on low-temperature datasets.
    THERMAL_RUNAWAY_LIMIT_C = 190.0  # °C
    THERMAL_RUNAWAY_LIMIT_K = 273.15 + THERMAL_RUNAWAY_LIMIT_C  # 463.15K
    PRINTING_TEMP_MIN_K = 430.0  # ~157°C; heuristic: indicates hotend is heating/printing
    NORMAL_TEMP_MIN = 300.0  # K
    NORMAL_TEMP_MAX = 315.0  # K
    NORMAL_RPM_MIN = 1200
    NORMAL_RPM_MAX = 1800
    NORMAL_TORQUE_MIN = 40.0  # Nm
    NORMAL_TORQUE_MAX = 60.0  # Nm
    TOOL_WEAR_LIMIT = 200  # minutes
    
    @staticmethod
    def detect_anomalies(sensor_data: Dict) -> List[Dict]:
        """
        Analyze sensor data and return detected anomalies.
        
        Args:
            sensor_data: Dict with keys: temperature, rpm, torque, tool_wear, failure_type
            
        Returns:
            List of anomaly dictionaries with type, severity, and description
        """
        anomalies = []
        
        temp_k = sensor_data.get('temperature', 0)
        rpm = sensor_data.get('rpm', 0)
        torque = sensor_data.get('torque', 0)
        tool_wear = sensor_data.get('tool_wear', 0)
        failure_type = sensor_data.get('status', 'Normal')
        
        # Convert temperature from Kelvin to Celsius for human-readable reporting
        temp_c = temp_k - 273.15 if isinstance(temp_k, (int, float)) else 0.0

        # 1. Thermal Runaway Detection (3D-printer hotend logic)
        # Detected if temperature is below 190°C *while* in a printing/heat-up regime.
        # We approximate "printing/heat-up" as: temp_k >= PRINTING_TEMP_MIN_K and rpm > 0.
        #
        # This avoids flagging every machine when temp_k is ~300K (27–42°C),
        # which is not a printing hotend temperature.
        if (
            rpm > 0
            and isinstance(temp_k, (int, float))
            and temp_k >= AnomalyDetector.PRINTING_TEMP_MIN_K
            and temp_k < AnomalyDetector.THERMAL_RUNAWAY_LIMIT_K
        ):
            anomalies.append({
                'type': 'Thermal Runaway',
                'code': 'TR-001',
                'severity': 'CRITICAL',
                'description': (
                    f'Hotend temperature is {temp_c:.1f}°C ({temp_k:.1f}K) during operation (RPM: {rpm}), '
                    f'which is below the {AnomalyDetector.THERMAL_RUNAWAY_LIMIT_C:.0f}°C minimum expected while printing/heat-up. '
                    'This indicates thermal runaway / heater not reaching setpoint.'
                ),
                'recommended_action': (
                    'Stop the machine. Inspect heater cartridge, thermistor seating/connection, and wiring harness. '
                    'Verify PSU output and mainboard heater MOSFET if applicable.'
                ),
            })
        
        # 2. Fan Failure Detection
        # Detected if RPM = 0 during operation (when temp indicates active printing)
        if temp_k > AnomalyDetector.NORMAL_TEMP_MIN and rpm == 0:
            anomalies.append({
                'type': 'Fan Failure',
                'code': 'FF-001',
                'severity': 'HIGH',
                'description': f'Fan RPM is 0 while temperature is {temp_k:.1f}K. The cooling fan is not operating, which can lead to overheating.',
                'recommended_action': 'Check fan power connection, debris blockage, and fan motor. Replace if necessary.'
            })
        
        # 3. Motor Strain Detection
        # Detected if Torque > Normal Limit
        if torque > AnomalyDetector.NORMAL_TORQUE_MAX:
            severity = 'CRITICAL' if torque > AnomalyDetector.NORMAL_TORQUE_MAX * 1.5 else 'HIGH'
            anomalies.append({
                'type': 'Motor Strain',
                'code': 'MS-001',
                'severity': severity,
                'description': f'Torque reading {torque:.1f} Nm exceeds normal operating range (40-60 Nm). This indicates excessive mechanical resistance or jam.',
                'recommended_action': 'Check for mechanical obstructions, belt tension, and motor condition. Reduce load if possible.'
            })
        
        # 4. Temperature Anomaly (Outside Normal Range)
        if temp_k < AnomalyDetector.NORMAL_TEMP_MIN or temp_k > AnomalyDetector.NORMAL_TEMP_MAX:
            if temp_k < AnomalyDetector.NORMAL_TEMP_MIN:
                issue = 'below'
                threshold = AnomalyDetector.NORMAL_TEMP_MIN
            else:
                issue = 'above'
                threshold = AnomalyDetector.NORMAL_TEMP_MAX
            
            anomalies.append({
                'type': 'Temperature Anomaly',
                'code': 'TA-001',
                'severity': 'MEDIUM',
                'description': f'Temperature {temp_k:.1f}K is {issue} normal operating range (300-315K).',
                'recommended_action': 'Verify thermistor calibration and heating system operation.'
            })
        
        # 5. Tool Wear Warning
        if tool_wear > AnomalyDetector.TOOL_WEAR_LIMIT:
            anomalies.append({
                'type': 'Tool Wear',
                'code': 'TW-001',
                'severity': 'MEDIUM',
                'description': f'Tool wear {tool_wear} minutes exceeds recommended limit of {AnomalyDetector.TOOL_WEAR_LIMIT} minutes.',
                'recommended_action': 'Schedule tool replacement to prevent failure.'
            })
        
        # 6. RPM Anomaly
        if rpm > 0 and (rpm < AnomalyDetector.NORMAL_RPM_MIN or rpm > AnomalyDetector.NORMAL_RPM_MAX):
            anomalies.append({
                'type': 'RPM Anomaly',
                'code': 'RPM-001',
                'severity': 'MEDIUM',
                'description': f'RPM {rpm} is outside normal operating range (1200-1800 RPM).',
                'recommended_action': 'Check fan motor, power supply, and control system.'
            })
        
        return anomalies
    
    @staticmethod
    def analyze_machine(machine_data: Dict) -> Dict:
        """
        Comprehensive analysis of a machine's sensor data.
        
        Returns:
            Dict with status, anomalies, and summary
        """
        anomalies = AnomalyDetector.detect_anomalies(machine_data)
        
        # Determine overall status
        if any(a['severity'] == 'CRITICAL' for a in anomalies):
            overall_status = 'CRITICAL'
        elif any(a['severity'] == 'HIGH' for a in anomalies):
            overall_status = 'WARNING'
        elif anomalies:
            overall_status = 'CAUTION'
        else:
            overall_status = 'NORMAL'
        
        return {
            'machine_id': machine_data.get('machine_id'),
            'model_name': machine_data.get('model_name', 'Unknown'),
            'status': overall_status,
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'timestamp': machine_data.get('timestamp', datetime.now())
        }
