"""
Routes pour l'interface d'administration des bâtiments.
"""

import logging
from flask import render_template, request, redirect, url_for, flash, abort
from src.admin import admin_bp
from src.db.building_dao import BuildingDAO, OperationNotAllowedException
from src.models.building import Building

# Configuration du logger
logger = logging.getLogger('admin.routes')

@admin_bp.route('/buildings')
def list_buildings():
    """
    Affiche la liste des bâtiments.
    """
    try:
        # Récupérer les paramètres de pagination
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = (page - 1) * limit
        
        # Récupérer les bâtiments
        dao = BuildingDAO()
        buildings = dao.list_buildings(limit=limit, offset=offset)
        
        return render_template('admin/buildings/list.html', buildings=buildings, page=page, limit=limit)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des bâtiments: {str(e)}")
        flash(f"Erreur: {str(e)}", "danger")
        return render_template('admin/buildings/list.html', buildings=[], page=1, limit=10)

@admin_bp.route('/buildings/new', methods=['GET', 'POST'])
def add_building():
    """
    Affiche le formulaire d'ajout de bâtiment et traite sa soumission.
    """
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            location = request.form.get('location', '').strip()
            email_gestionnaire = request.form.get('email_gestionnaire', '').strip() or None
            notes = request.form.get('notes', '').strip() or None
            qr_code_number = request.form.get('qr_code_number', '').strip() or None
            
            # Valider les données
            if not location:
                flash("L'adresse du bâtiment est obligatoire.", "danger")
                return render_template('admin/buildings/form.html')
            
            # Créer l'objet Building
            building = Building(
                location=location,
                email_gestionnaire=email_gestionnaire,
                notes=notes,
                qr_code_number=qr_code_number
            )
            
            # Enregistrer le bâtiment
            dao = BuildingDAO()
            building = dao.create_building(building)
            
            flash(f"Bâtiment ajouté avec succès. QR Code: {building.qr_code_number}", "success")
            return redirect(url_for('admin.list_buildings'))
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du bâtiment: {str(e)}")
            flash(f"Erreur: {str(e)}", "danger")
            return render_template('admin/buildings/form.html')
    
    # Méthode GET: afficher le formulaire
    return render_template('admin/buildings/form.html')

@admin_bp.route('/buildings/<int:building_id>')
def view_building(building_id):
    """
    Affiche les détails d'un bâtiment.
    """
    try:
        dao = BuildingDAO()
        building = dao.get_building_by_id(building_id)
        
        if not building:
            flash(f"Bâtiment avec ID {building_id} non trouvé.", "danger")
            return redirect(url_for('admin.list_buildings'))
        
        return render_template('admin/buildings/view.html', building=building)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du bâtiment {building_id}: {str(e)}")
        flash(f"Erreur: {str(e)}", "danger")
        return redirect(url_for('admin.list_buildings'))

@admin_bp.route('/buildings/<int:building_id>/edit', methods=['GET', 'POST'])
def edit_building(building_id):
    """
    Affiche le formulaire de modification d'un bâtiment et traite sa soumission.
    Note: Dans l'implémentation actuelle, la modification des bâtiments est interdite.
    """
    flash("La modification des bâtiments n'est pas autorisée dans cette version.", "warning")
    return redirect(url_for('admin.view_building', building_id=building_id))

@admin_bp.route('/buildings/<int:building_id>/delete', methods=['POST'])
def delete_building(building_id):
    """
    Supprime un bâtiment.
    Note: Dans l'implémentation actuelle, la suppression des bâtiments est interdite.
    """
    flash("La suppression des bâtiments n'est pas autorisée dans cette version.", "warning")
    return redirect(url_for('admin.view_building', building_id=building_id))
