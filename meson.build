project('grapik-quran',
          version: '0.1.0-alpha.3',
    meson_version: '>= 0.54.0',
  default_options: [ 'warning_level=2',
                   ],
)

i18n = import('i18n')


subdir('data')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
