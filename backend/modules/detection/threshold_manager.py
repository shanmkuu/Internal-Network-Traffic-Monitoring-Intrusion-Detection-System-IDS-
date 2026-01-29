import time
from collections import defaultdict

class ThresholdManager:
    """
    Manages alert thresholds.
    Supports: threshold: type limit|both, track by_src|by_dst, count N, seconds T
    """
    def __init__(self):
        # Key: (sid, track_value), Value: {count, start_time, last_alert}
        self.trackers = {} 
        self.default_timeout = 60

    def check_threshold(self, rule, src_ip, dst_ip):
        """
        Returns True if alert should be generated, False if suppressed.
        """
        options = rule.get('options', {})
        if 'threshold' not in options:
            return True # No threshold, always alert (or default global limit)

        # Parse threshold string: "type limit, track by_src, count 1, seconds 60"
        # Since our parser might just return the raw string or dict, let's assume raw string for now
        # because the RuleParser handles simple key:value.
        # Suricata syntax: threshold: type <type>, track <track>, count <count>, seconds <seconds>
        # Our parser might return just the string value if it was inside options like threshold: ...;
        
        t_str = options['threshold']
        
        # Simple parsing logic
        params = {}
        for part in t_str.split(','):
            part = part.strip()
            if ' ' in part:
                k, v = part.split(' ', 1)
                params[k] = v
        
        type_ = params.get('type', 'limit')
        track = params.get('track', 'by_src')
        count = int(params.get('count', 1))
        seconds = int(params.get('seconds', 60))
        sid = options.get('sid', 0)

        # Determine tracking key
        track_key = src_ip if track == 'by_src' else dst_ip
        
        # Unique identifier for this rule+target
        tracker_id = (sid, track_key)
        
        now = time.time()
        
        if tracker_id not in self.trackers:
            self.trackers[tracker_id] = {
                "count": 0,
                "start_time": now,
                "last_alert": 0
            }
            
        t_state = self.trackers[tracker_id]
        
        # Reset if window expired
        if now - t_state['start_time'] > seconds:
            t_state['count'] = 0
            t_state['start_time'] = now
            
        t_state['count'] += 1
        
        if type_ == 'limit':
            # Alert at most 'count' times within 'seconds'
            if t_state['count'] <= count:
                return True
            else:
                return False
                
        elif type_ == 'threshold':
            # Alert only after 'count' times
             if t_state['count'] >= count:
                 # Logic for "at least X times" - usually creates one alert?
                 # Or alerts for every packet after? 
                 # Suricata "threshold" type alerts on the Nth time.
                 return True
                 
        return True # Default allow

threshold_manager = ThresholdManager()
