"""
Pre-600 BCE Subcontinent APM Discovery GIS - QGIS Plugin Entrypoint.
Initializes the classFactory for QGIS 3.x integration.
"""

def classFactory(iface):
    """Load APMPlugin class from file apm_plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from qgis_plugin.apm_plugin import APMPlugin
    return APMPlugin(iface)
