public class VoieCompagnonAnimal extends Voie {
    public VoieCompagnonAnimal() {
        super("Voie du compagnon animal");
        competences.add(new Competence("Odorat", 1));
        competences.add(new Competence("Surveillance", 2));
        competences.add(new Competence("Combat", 3));
        competences.add(new Competence("Empathie animale", 4));
    }
}
