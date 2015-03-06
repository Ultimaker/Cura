hips_low_settings = [('infill_speed', '70'),
					 ('inset0_speed', '40'),
					 ('insetx_speed', '45')]
hips_normal_settings = [('infill_speed', '50'),
						('inset0_speed', '30'),
						('insetx_speed', '35')]
hips_high_settings = [('infill_speed', '30'),
					  ('inset0_speed', '20'),
					  ('insetx_speed', '25')]

abs_low_settings = [('infill_speed', '60'),
					('inset0_speed', '50'),
					('insetx_speed', '55'),
					('cool_min_layer_time', '15')]
abs_normal_settings = [('infill_speed', '55'),
					   ('inset0_speed', '45'),
					   ('insetx_speed', '50'),
					   ('cool_min_layer_time', '15')]
abs_high_settings = [('infill_speed', '40'),
					 ('inset0_speed', '30'),
					 ('insetx_speed', '35'),
					 ('cool_min_layer_time', '20')]

pla_low_settings = [('infill_speed', '80'),
					('inset0_speed', '60'),
					('insetx_speed', '70'),
					('cool_min_layer_time', '15'),
					('cool_min_feedrate', '15')]
pla_normal_settings = [('infill_speed', '60'),
					   ('inset0_speed', '50'),
					   ('insetx_speed', '55'),
					   ('cool_min_layer_time', '15'),
					   ('cool_min_feedrate', '10')]
pla_high_settings = [('infill_speed', '50'),
					 ('inset0_speed', '40'),
					 ('insetx_speed', '45'),
					 ('cool_min_layer_time', '20'),
					 ('cool_min_feedrate', '5')]

# LulzBot TAZ 5 slice settings for use with the simple slice selection.
lulzbot_taz5_settings = [{'Ini': 'taz5'},
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
						  'Settings': pla_high_settings},

						 {'Profile': '2_normal',
						  'Settings': [('layer_height', '0.22'),
									   ('solid_layer_thickness', '0.88')]},
						 {'Material': '3_pla', 'Profile': '2_normal',
						  'Settings': [('layer_height', '0.21'),
									   ('solid_layer_thickness', '0.84')]},

						 {'Profile': '3_high',
						  'Settings': [('layer_height', '0.14'),
									   ('solid_layer_thickness', '0.7')]},
						 {'Material': '2_abs', 'Profile': '3_high',
						  'Settings': [('layer_height', '0.16'),
									   ('solid_layer_thickness', '0.74')]}]
