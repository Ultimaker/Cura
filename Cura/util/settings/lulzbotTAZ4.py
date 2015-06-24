hips_low_settings = [('fan_full_height', '1'),
					 ('fan_speed', '25'),
					 ('fan_speed_max', '30')]
hips_normal_settings = [('skirt_minimal_length', '250'),
						('fan_full_height', '0.35'),
						('fan_speed', '50'),
						('fan_speed_max', '50')]
hips_high_settings = [('fan_full_height', '0.56'),
					  ('fan_speed', '50'),
					  ('fan_speed_max', '60'),
					  ('cool_min_feedrate', '8')]

abs_low_settings = [('fan_full_height', '5'),
					('fan_speed', '25'),
					('fan_speed_max', '30')]
abs_normal_settings = [('fan_speed', '25'),
					   ('fan_speed_max', '25'),
					   ('fill_overlap', '5')]
abs_high_settings = [('retraction_hop', '0.1'),
					 ('fan_full_height', '5'),
					 ('fan_speed', '40'),
					 ('fan_speed_max', '75')]


pla_low_settings = [('skirt_minimal_length', '250'),
					('fan_full_height', '1'),
					('fan_speed', '75'),
					('cool_min_feedrate', '15'),
					('fill_overlap', '0')]
pla_normal_settings = [('retraction_hop', '0.1'),
					   ('skirt_minimal_length', '250'),
					   ('fan_full_height', '1'),
					   ('fan_speed', '75'),
					   ('cool_min_feedrate', '15')]
pla_high_settings = [('skirt_minimal_length', '0'),
					 ('fan_full_height', '0.28'),
					 ('fill_overlap', '10')]

# LulzBot TAZ 4 slice settings for use with the simple slice selection.
lulzbot_taz4_settings = [{'Ini': 'taz4'},
						 {'Material': '1_hips', 'Profile': '1_low',
						  'Settings': hips_low_settings},
						 {'Material': '1_hips', 'Profile': '2_normal',
						  'Settings': hips_normal_settings},
						 {'Material': '1_hips', 'Profile': '3_high',
						  'Settings': hips_high_settings},

						 {'Material': '2_abs', 'Profile': '1_low',
						  'Settings': abs_low_settings},
						 {'Material': '2_abs', 'Profile': '2_normal',
						  'Settings': abs_normal_settings},
						 {'Material': '2_abs', 'Profile': '3_high',
						  'Settings': abs_high_settings},

						 {'Material': '3_pla', 'Profile': '1_low',
						  'Settings': pla_low_settings},
						 {'Material': '3_pla', 'Profile': '2_normal',
						  'Settings': pla_normal_settings},
						 {'Material': '3_pla', 'Profile': '3_high',
						  'Settings': pla_high_settings}]
