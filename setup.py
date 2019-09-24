from distutils.core import setup

pkg = 'SystemPlugins.NewVirtualKeyBoard'
setup (name = 'enigma2-plugin-systemplugins-newvirtualkeyboard',
       version = '1.0',
       description = 'New VirtualKeyBoard Style.',
       packages = [pkg],
       package_dir = {pkg: 'usr'},
       package_data = {pkg: ['plugin.png', '*/*.png']},
      )
