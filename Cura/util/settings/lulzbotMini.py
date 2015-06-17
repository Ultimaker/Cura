hips_low_settings = [('print_speed', '50'),
					 ('infill_speed', '70'),
					 ('inset0_speed', '40'),
					 ('insetx_speed', '45'),
					 ('cool_min_layer_time', '15'),
					 ('cool_min_feedrate', '10')]

hips_normal_settings = [('print_speed', '50'),
						('infill_speed', '60'),
						('inset0_speed', '30'),
						('insetx_speed', '35'),
						('cool_min_layer_time', '15'),
						('cool_min_feedrate', '10')]

hips_high_settings = [('print_speed', '30'),
					  ('infill_speed', '30'),
					  ('inset0_speed', '20'),
					  ('insetx_speed', '25'),
					  ('cool_min_layer_time', '20'),
					  ('cool_min_feedrate', '5')]

abs_low_settings = [('print_speed', '85'),
					('infill_speed', '60'),
					('inset0_speed', '50'),
					('insetx_speed', '55'),
					('cool_min_feedrate', '10')]

abs_normal_settings = [('print_speed', '50'),
					   ('infill_speed', '55'),
					   ('inset0_speed', '45'),
					   ('insetx_speed', '50'),
					   ('cool_min_feedrate', '10')]

abs_high_settings = [('print_speed', '50'),
					 ('infill_speed', '40'),
					 ('inset0_speed', '30'),
					 ('insetx_speed', '35'),
					 ('cool_min_feedrate', '5')]

pla_low_settings = [('cool_min_feedrate', '10'),
					('infill_speed', '40'),
					('inset0_speed', '30'),
					('insetx_speed', '35')]
pla_normal_settings = [('cool_min_feedrate', '10'),
					   ('infill_speed', '40'),
					   ('inset0_speed', '30'),
					   ('insetx_speed', '35')]
pla_high_settings = [('cool_min_feedrate', '5'),
					 ('infill_speed', '30'),
					 ('inset0_speed', '25'),
					 ('insetx_speed', '27')]

# LulzBot Mini slice settings for use with the simple slice selection.
lulzbot_mini_settings = [{'Ini': 'mini'},
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

						 {'Profile': '3_high',
						  'Settings': [('layer_height', '0.18')]},
						 {'Material': '3_pla', 'Profile': '3_high',
						  'Settings': [('layer_height', '0.14')]}]
