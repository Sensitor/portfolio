public class VoieMagieProtectrice extends Voie {
    public VoieMagieProtectrice() {
        super("Voie de la magie protectrice");
        competences.add(new Competence("Armure du mage", 1));
        competences.add(new Competence("Chute ralentie", 2));
        competences.add(new Competence("Flou", 3));
        competences.add(new Competence("Cercle de protection", 4));
    }
}
