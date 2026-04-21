public class VoieMagieDestructrice extends Voie {
    public VoieMagieDestructrice() {
        super("Voie de la magie destructrice");
        competences.add(new Competence("Projectile magique", 1));
        competences.add(new Competence("Rayon affaiblissant", 2));
        competences.add(new Competence("Fleche enflammee", 3));
        competences.add(new Competence("Boule de feu", 4));
    }
}
